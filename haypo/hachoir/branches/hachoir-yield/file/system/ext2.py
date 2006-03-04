"""
EXT2 (Linux) file system parser.

Sources:
- EXT2FS source code
  http://ext2fsd.sourceforge.net/
- Analysis of the Ext2fs structure
  http://www.nondot.org/sabre/os/files/FileSystems/ext2fs/
"""

from text_handler import unixTimestamp
from field import FieldSet, Integer, String
from tools import humanDuration, getUnixRWX, humanFilesize

class DirectoryEntry(FieldSet):
    file_type = {
        1: "Regular",
        2: "Directory",
        3: "Char. dev.",
        4: "Block dev.",
        5: "Fifo",
        6: "Socket",
        7: "Symlink",
        8: "Max"
    }
    endian = "<"
    
    def createFields(self):
        yield Integer("inode", "uint32", "Inode")
        yield Integer("rec_len", "uint16", "Record length")
        name_length = self.doRead("name_len", "B", "Name length", (FormatChunk, "uint8")).value
        yield Integer("file_type", "uint8", DirectoryEntry.file_type, "File type")
        self.read("name", "File name", (FormatChunk, "string[%u]" % name_length))
        size = self["rec_len"]-8-name_length 
        if size != 0:
            self.read("padding", "Padding", (FormatChunk, "string[%u]" % size))

    def updateParent(self, chunk):        
        name = self["name"].strip("\0")
        if name != "":
            desc = "Directory entry: %s" % name
        else:
            desc = "Directory entry (empty)"
        chunk.description = desc
        self.setDescription(desc)

class Inode(FieldSet):
    name = {
        1: "list of bad blocks",
        2: "Root directory",
        3: "ACL inode",
        4: "ACL inode",
        5: "Boot loader",
        6: "Undelete directory",
        8: "EXT3 journal"
    }

    endian = "<"
    static_size = (68 + 15*4)*8

    def __init__(self, parent, name, stream, index, description=None):
        self.index = index
        FieldSet.__init__(self, parent, name, stream, description)
        
        if self.description == None:
            desc = "Inode %s: " % self.index

            if 11 <= self.index:
                size = humanFilesize(self["size"].value)
                desc += "file, size=%s, mode=%s" % (size, self["mode"].display)
            else:
                if self.index in Inode.name:
                    desc += Inode.name[self.index]
                    if self.index == 2:
                        desc += " (%s)" % getUnixRWX(self["mode"].value)
                else:
                    desc += "special"
                if self["size"].value == 0:
                    desc += " (unused)"
            self.description = desc

    def createFields(self):
        self.read("mode", "Mode", (FormatChunk, "uint16"), {"post": self.postMode})
        yield Integer("uid", "uint16", "User ID")
        yield Integer("size", "uint32", "File size (in bytes)")
        yield Integer("atime", "uint32", "Last access time") # {"post": unixTimestamp}
        yield Integer("ctime", "uint32", "Creation time") # {"post": unixTimestamp}
        yield Integer("mtime", "uint32", "Last modification time") # {"post": unixTimestamp}
        yield Integer("dtime", "uint32", "Delete time") #  {"post": unixTimestamp}
        yield Integer("gid", "uint16", "Group ID")
        yield Integer("links_count", "uint16", "Links count")
        yield Integer("blocks", "uint32", "Number of blocks")
        yield Integer("flags", "uint32", "Flags")
        yield Integer("reserved1", "uint32", "Reserved")
        for i in range(0,15):
            yield Integer("block[]", "uint32", "Block %i" % i)
        yield Integer("version", "uint32", "Version")
        yield Integer("file_acl", "uint32", "File ACL")
        yield Integer("dir_acl", "uint32", "Directory ACL")
        yield Integer("faddr", "uint32", "Block where the fragment of the file resides")
        
        os = self["/superblock/creator_os"].value
        if os == SuperBlock.OS_LINUX:
            yield Integer("frag", "uint8", "Number of fragments in the block")
            yield Integer("fsize", "uint8", "Fragment size")
            yield Integer("padding", "uint16", "Padding")
            yield Integer("uid_high", "uint16", "High 16 bits of user ID")
            yield Integer("gid_high", "uint16", "High 16 bits of group ID")
            yield Integer("reserved", "uint32", "Reserved")
        elif os == SuperBlock.OS_HURD:
            yield Integer("frag", "uint8", "Number of fragments in the block")
            yield Integer("fsize", "uint8", "Fragment size")
            yield Integer("mode_high", "uint16", "High 16 bits of mode")
            yield Integer("uid_high", "uint16", "High 16 bits of user ID")
            yield Integer("gid_high", "uint16", "High 16 bits of group ID")
            yield Integer("author", "uint32", "Author ID (?)")
        else:
            yield String("raw", "string[12]", "Reserved")

    def postMode(self, chunk):
        mode = chunk.value
        text = ""
        if mode & 0100000 != 0:
            text = "regular (%s)" % getUnixRWX(mode)
        elif mode & 0040000:
            text = "directory (%s)" % getUnixRWX(mode)
        elif mode & 0020000:
            text = "char. dev."
        elif mode & 0060000:
            text = "block dev."
        elif mode & 0010000:
            text = "fifo"
        elif mode & 0120000:
            text = "sym. link"
        elif mode & 0140000:
            text = "socket"
        elif mode == 0:
            text = "(empty)"
        else:
            text = "???"
        return text

class Bitmap(FieldSet):
    def __init__(self, parent, name, stream, count, start, description=None):
        if description != None:
            description = "%s: %s items" % (description, count)
        FieldSet.__init__(self, parent, name, stream, description)
        assert (count % 8) == 0
        self._size = count / 8
        self.start = start
        self.count = count

    def createFields(self):
        yield String("block_bitmap", "string[%u]" % self._size, "Bitmap")

#    def showFree(self, type="Block"):
#        data = self["block_bitmap"]
#        cpt = self.start
#        for octet in data:
#            octet = ord(octet)
#            mask = 1
#            for i in range(0,8):
#                if octet & mask == 0:
#                    print "%s %s free." % (type, cpt)
#                cpt = cpt + 1
#                mask = mask << 1

BlockBitmap = Bitmap
InodeBitmap = Bitmap

class GroupDescriptor(FieldSet):
    endian = "<"
    static_size = 32*8

    def __init__(self, parent, name, stream, index, description="Group descriptor"):
        FieldSet.__init__(self, parent, name, stream, description)
        self.index = index

        # Set description
        superblock = self["/superblock"]
        blocks_per_group = superblock["blocks_per_group"].value
        start = self.index * blocks_per_group
        end = start + blocks_per_group 
        self.description = "Group descriptor: blocks %s-%s" % (start, end)

    def createFields(self):
        yield Integer("block_bitmap", "uint32", "Points to the blocks bitmap block")
        yield Integer("inode_bitmap", "uint32", "Points to the inodes bitmap block")
        yield Integer("inode_table", "uint32", "Points to the inodes table first block")
        yield Integer("free_blocks_count", "uint16", "Number of free blocks")
        yield Integer("free_inodes_count", "uint16", "Number of free inodes")
        yield Integer("used_dirs_count", "uint16", "Number of inodes allocated to directories")
        yield Integer("padding", "uint16", "Padding")
        yield String("reserved", "string[12]", "Reserved")
   
class SuperBlock(FieldSet):
    error_handling = {
        1: "Continue"
    }
    OS_LINUX = 0
    OS_HURD = 1
    os_name = {
        0: "Linux",
        1: "Hurd",
        2: "Masix",
        3: "FreeBSD",
        4: "Lites",
        5: "WinNT"
    }
    state = {
        1: "Valid",
        2: "Error"
    }
 
    static_size = 433*8
 
    def __init__(self, parent, name, stream, description="Super block"):
        FieldSet.__init__(self, parent, name, stream, description)
        if self["feature_compat"].value & 4 == 4:
            type = "ext3"
        else:
            type = "ext2"
        self.description = "Superblock: %s file system" % type

    def createFields(self):
        yield Integer("inodes_count", "uint32", "Inodes count")
        yield Integer("blocks_count", "uint32", "Blocks count")
        yield Integer("r_blocks_count", "uint32", "Reserved blocks count")
        yield Integer("free_blocks_count", "uint32", "Free blocks count")
        yield Integer("free_inodes_count", "uint32", "Free inodes count")
        yield Integer("first_data_block", "uint32", "First data block")
        if self["first_data_block"].value != 0:
            raise ParserError(
                "Stream doesn't looks like EXT2/EXT3 partition "
                "(first data block is %s instead of 0)" %
                self["first_data_block"].value)                
        yield Integer("log_block_size", "uint32", "Block size")
        yield Integer("log_frag_size", "uint32", "Fragment size")
        yield Integer("blocks_per_group", "uint32", "Blocks per group")
        yield Integer("frags_per_group", "uint32", "Fragments per group")
        yield Integer("inodes_per_group", "uint32", "Inodes per group")
        yield Integer("mtime", "uint32", "Mount time") #  {"post": unixTimestamp}
        yield Integer("wtime", "uint32", "Write time") #  {"post": unixTimestamp}
        yield Integer("mnt_count", "uint16", "Mount count")
        yield Integer("max_mnt_count", "int16", "Max mount count")
        yield String("magic", "string[2]", "Magic number (0x53EF)")
        if self["magic"].value != "\x53\xEF":
            raise ParserError(
                "Stream doesn't looks like EXT2/EXT3 partition "
                "(invalid magic value)")
        yield Integer("state", "uint16", SuperBlock.state, "File system state")
        yield Enum("errors", "uint16", SuperBlock.error_handling, "Behaviour when detecting errors")
        yield Integer("minor_rev_level", "uint16", "Minor revision level")
        yield Integer("last_check", "uint32", "Time of last check") #  {"post": unixTimestamp}
        yield Integer("check_interval", "uint32", "Maximum time between checks") #  {"post": self.postMaxTime}
        yield Enum("creator_os", "uint32", SuperBlock.os_name, "Creator OS")        
        yield Integer("rev_level", "uint32", "Revision level")
        yield Integer("def_resuid", "uint16", "Default uid for reserved blocks")
        yield Integer("def_resgid", "uint16", "Default guid for reserverd blocks")
        yield Integer("first_ino", "uint32", "First non-reserved inode")
        yield Integer("inode_size", "uint16", "Size of inode structure")
        if self["inode_size"].value != (68 + 15*4):
            raise ParserError(
                "EXT2/EXT3 parser error: inode of size %s are not supported" \
                % self["inode_size"].value)
        yield Integer("block_group_nr", "uint16", "Block group # of this superblock")
        yield Integer("feature_compat", "uint32", "Compatible feature set")
        yield Integer("feature_incompat", "uint32", "Incompatible feature set")
        yield Integer("feature_ro_compat", "uint32", "Read-only compatible feature set")
        yield String("uuid", "string[16]", "128-bit uuid for volume")
        yield String("volume_name", "string[16]", "Volume name")
        yield String("last_mounted", "string[64]", "Directory where last mounted")
        yield Integer("compression", "uint32", "For compression (algorithm usage bitmap)")
        yield Integer("prealloc_blocks", "uint8", "Number of blocks to try to preallocate")
        yield Integer("prealloc_dir_blocks", "uint8", "Number to preallocate for directories")
        yield Integer("padding", "uint16", "Padding")
        yield String("journal_uuid", "string[16]", "uuid of journal superblock")
        yield Integer("journal_inum", "uint32", "inode number of journal file")
        yield Integer("journal_dev", "uint32", "device number of journal file")
        yield Integer("last_orphan", "uint32", "start of list of inodes to delete")
        yield String("reserved", "string[197]", "Padding to the end of the block")

        # Calculate number of groups
        blocks_per_group = self["blocks_per_group"].value
        self.group_count = (self["blocks_count"].value - self["first_data_block"].value + (blocks_per_group - 1)) / blocks_per_group
 
#    def postMaxTime(self, chunk):
#        return humanDuration(chunk.value * 1000)

class GroupDescriptors(FieldSet):
    def __init__(self, parent, name, stream, start, count, description=None):
        if description == None:
            description = "Group descriptors: %s items" % count
        FieldSet.__init__(self, parent, name, stream, description)
        self.start = start
        self.count = count

    def createFields(self):
        for index in range(0, self.count):
            yield GroupDescriptor(self, "group[]", self.stream, index)

    def getGroup(self, index):
        return self["group[%s]" % (self.start + index)]

class InodeTable(FieldSet):
    def __init__(self, parent, name, stream, start, count, description=None):
        if description == None:
            description = "Inode table: %s inodes" % count
        FieldSet.__init__(self, parent, name, stream, description)
        self.start = start
        self.count = count

    def createFields(self):
        for index in range(self.start, self.start+self.count):
            yield Inode(self, "inode[]", index, description="Inode %s" % index)

    def __getitem__(self, index):
        index = index - self.start - 1
        return self.getChunk("inode[%u]" % index).getFilter()

def testSuperblock(stream):
    oldpos = stream.tell()
    stream.seek(56, 1)
    magic = stream.getN(2)    
    stream.seek(oldpos)
    return (magic == "\x53\xEF")

class Group(FieldSet):
    def __init__(self, stream, parent, index, description=None):
        if description == None:
            description = "Group %u" % index
        FieldSet.__init__(self, parent, name, stream, description)
        self.index = index

    def createFields(self):
        group = self["../group_desc"].getGroup(index)
        superblock = self["/superblock"]
        block_size = self["/"].block_size
    
        # Read block bitmap
        self.superblock_copy = False
        if testSuperblock(stream):
            self.superblock_copy = True
            yield SuperBlock(self, "superblock_copy", self.stream, "Superblock")
        self.seek(group["block_bitmap"] * block_size)
            
        count = superblock["blocks_per_group"]
        yield BlockBitmap(self, "block_bitmap[]", self.stream, count, 0, "Block bitmap")

        # Read inode bitmap
        assert (group["inode_bitmap"] * block_size) == stream.tell()
        count = superblock["inodes_per_group"]
        self.read("inode_bitmap[]", "Inode bitmap", (InodeBitmap, "Inode bitmap", count, 1), {"size": count / 8})
        addr = stream.tell() % 4096
        if addr != 0:
            addr = stream.tell() + (4096 - addr % 4096)
            self.seek(addr)
             
        count = superblock["inodes_per_group"]
        size = superblock["inode_size"] * count
        inode_index = 1 + index * count
        self.read("inode_table[]", "Inode table", (InodeTable, inode_index, count), {"size": size})

        size = (index+1) * superblock["blocks_per_group"] * block_size
        if stream.getSize() < size:
            size = stream.getSize()
        size = size - stream.tell() 
        self.read("data", "Data", (FormatChunk, "string[%u]" % size))

    def updateParent(self, chunk):
        desc = "Group %s: %s" % (self.index, humanFilesize(self.getSize()))
        if self.superblock_copy:
            desc = desc + " (with superblock copy)"
        chunk.description = desc 

    def seek(self, to):
        size = to - self.getStream().tell()
        assert 0 <= size
        if 0 < size:
            self.read("raw[]", "Raw", (FormatChunk, "string[%u]" % size))

class EXT2_FS(FieldSet):
    """
    Parse an EXT2 or EXT3 partition.

    Attributes:
       * block_size: Size of a block (in bytes)

    Fields:
       * superblock: Most important block, store most important informations
       * ...
    """
    mime_types = "hachoir/fs-ext2"

    def __init__(self, parent, name, stream, description="EXT2 file system"):
        FieldSet.__init__(self, parent, name, stream, description)

    def createFields(self):
        # Skip something (what is stored here? MBR?) 
        self.seek(1024) 
        
        # Read superblock
        superblock = SuperBlock(self, "superblock", self.stream)
        yield superblock
        self.block_size = 1024 << superblock["log_block_size"].value # in bytes

        # Read groups' descriptor
        self.seek(4096) 
        groups = GroupDescriptors(self, "group_desc", self.stream, 0, superblock.group_count)
        yield groups

        # Read groups
        address = groups.getGroup(0)["block_bitmap"].value * self.block_size * 8
        self.seek(address)
        for i in range(0, superblock.group_count):
            self.read("group[]", "Group", (Group, i))

        # Padding (?)
        size = stream.getSize() - stream.tell()
        if size != 0:
            self.read("end", "End (raw)", (FormatChunk, "string[%u]" % size))

    def seek(self, to):
        size = to - self.getStream().tell()
        assert 0 <= size
        if 0 < size:
            yield String(self, "raw[]", "string[%u]" % size, raw)

#    def readDirectory(self, inode):
#        stream = self.getStream()
#        block_index = 0
#        while True:
#            assert block_index < 12
#            block = inode["block[%u]" % block_index]
#            if block == 0:
#                return
#            self.seek(block * self.block_size)
#
#            total = 0
#            while total < self.block_size:
#                entry = self.doRead("directory[]", "Directory entry", (DirectoryEntry,))
#                if entry["inode"] == 0:
#                    return
#                total = total + entry.getSize()
#            assert total == self.block_size
#            block_index = block_index + 1

