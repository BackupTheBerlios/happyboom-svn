"""
EXT2 (Linux) file system parser.

Sources:
- EXT2FS source code
  http://ext2fsd.sourceforge.net/
- Analysis of the Ext2fs structure
  http://www.nondot.org/sabre/os/files/FileSystems/ext2fs/
"""

from text_handler import unixTimestamp
from field import FieldSet, Integer, Enum, String, ParserError
from tools import humanDuration, getUnixRWX, humanFilesize
from bits import str2hex

class FieldSetWithSeek(FieldSet):
    def seekField(self, to):
        size = to - self._total_field_size 
        assert 0 <= size
        if 0 < size:
            assert (size % 8) == 0
            return String(self, "raw[]", "string[%u]" % (size / 8))
        else:
            return None

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

    # TODO: write constructor to set: self._size = self["rec_len"].value * 8 (or something like that)
    
    def createFields(self):
        yield Integer(self, "inode", "uint32", "Inode")
        yield Integer(self, "rec_len", "uint16", "Record length")
        name_length = Integer(self, "name_len", "B", "Name length", (FormatChunk, "uint8")).value
        yield name_length
        yield Enum(self, "file_type", "uint8", DirectoryEntry.file_type, "File type")
        yield String(self, "name", "string[%u]" % name_length, "File name")
        size = self["rec_len"].value-8-name_length 
        if size != 0:
            yield String(self, "padding", "string[%u]" % size, "Padding")

#  TODO: Re-enable that, maybe using event 'all fields are read'
#    def updateParent(self, chunk):        
#        name = self["name"].strip("\0")
#        if name != "":
#            desc = "Directory entry: %s" % name
#        else:
#            desc = "Directory entry (empty)"
#        chunk.description = desc
#        self.setDescription(desc)

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
        yield Integer(self, "mode", "uint16", "Mode") # {"post": self.postMode}
        yield Integer(self, "uid", "uint16", "User ID")
        yield Integer(self, "size", "uint32", "File size (in bytes)")
        yield Integer(self, "atime", "uint32", "Last access time") # {"post": unixTimestamp}
        yield Integer(self, "ctime", "uint32", "Creation time") # {"post": unixTimestamp}
        yield Integer(self, "mtime", "uint32", "Last modification time") # {"post": unixTimestamp}
        yield Integer(self, "dtime", "uint32", "Delete time") #  {"post": unixTimestamp}
        yield Integer(self, "gid", "uint16", "Group ID")
        yield Integer(self, "links_count", "uint16", "Links count")
        yield Integer(self, "blocks", "uint32", "Number of blocks")
        yield Integer(self, "flags", "uint32", "Flags")
        yield Integer(self, "reserved1", "uint32", "Reserved")
        for i in range(0,15):
            yield Integer(self, "block[]", "uint32", "Block %i" % i)
        yield Integer(self, "version", "uint32", "Version")
        yield Integer(self, "file_acl", "uint32", "File ACL")
        yield Integer(self, "dir_acl", "uint32", "Directory ACL")
        yield Integer(self, "faddr", "uint32", "Block where the fragment of the file resides")
        
        os = self["/superblock/creator_os"].value
        if os == SuperBlock.OS_LINUX:
            yield Integer(self, "frag", "uint8", "Number of fragments in the block")
            yield Integer(self, "fsize", "uint8", "Fragment size")
            yield Integer(self, "padding", "uint16", "Padding")
            yield Integer(self, "uid_high", "uint16", "High 16 bits of user ID")
            yield Integer(self, "gid_high", "uint16", "High 16 bits of group ID")
            yield Integer(self, "reserved", "uint32", "Reserved")
        elif os == SuperBlock.OS_HURD:
            yield Integer(self, "frag", "uint8", "Number of fragments in the block")
            yield Integer(self, "fsize", "uint8", "Fragment size")
            yield Integer(self, "mode_high", "uint16", "High 16 bits of mode")
            yield Integer(self, "uid_high", "uint16", "High 16 bits of user ID")
            yield Integer(self, "gid_high", "uint16", "High 16 bits of group ID")
            yield Integer(self, "author", "uint32", "Author ID (?)")
        else:
            yield String(self, "raw", "string[12]", "Reserved")

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
        self._size = count
        self.start = start
        self.count = count

    def createFields(self):
        yield String(self, "block_bitmap", "string[%u]" % self._size, "Bitmap")

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
        yield Integer(self, "block_bitmap", "uint32", "Points to the blocks bitmap block")
        yield Integer(self, "inode_bitmap", "uint32", "Points to the inodes bitmap block")
        yield Integer(self, "inode_table", "uint32", "Points to the inodes table first block")
        yield Integer(self, "free_blocks_count", "uint16", "Number of free blocks")
        yield Integer(self, "free_inodes_count", "uint16", "Number of free inodes")
        yield Integer(self, "used_dirs_count", "uint16", "Number of inodes allocated to directories")
        yield Integer(self, "padding", "uint16", "Padding")
        yield String(self, "reserved", "string[12]", "Reserved")
   
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
    endian = "<"
 
    def __init__(self, parent, name, stream, description="Super block"):
        FieldSet.__init__(self, parent, name, stream, description)
        if self["feature_compat"].value & 4 == 4:
            type = "ext3"
        else:
            type = "ext2"
        self.description = "Superblock: %s file system" % type
        self._group_count = None

    def createFields(self):
        yield Integer(self, "inodes_count", "uint32", "Inodes count")
        yield Integer(self, "blocks_count", "uint32", "Blocks count")
        yield Integer(self, "r_blocks_count", "uint32", "Reserved blocks count")
        yield Integer(self, "free_blocks_count", "uint32", "Free blocks count")
        yield Integer(self, "free_inodes_count", "uint32", "Free inodes count")
        yield Integer(self, "first_data_block", "uint32", "First data block")
        if self["first_data_block"].value != 0:
            raise ParserError(
                "Stream doesn't looks like EXT2/EXT3 partition "
                "(first data block is %s instead of 0)" %
                self["first_data_block"].value)                
        yield Integer(self, "log_block_size", "uint32", "Block size")
        yield Integer(self, "log_frag_size", "uint32", "Fragment size")
        yield Integer(self, "blocks_per_group", "uint32", "Blocks per group")
        yield Integer(self, "frags_per_group", "uint32", "Fragments per group")
        yield Integer(self, "inodes_per_group", "uint32", "Inodes per group")
        yield Integer(self, "mtime", "uint32", "Mount time") #  {"post": unixTimestamp}
        yield Integer(self, "wtime", "uint32", "Write time") #  {"post": unixTimestamp}
        yield Integer(self, "mnt_count", "uint16", "Mount count")
        yield Integer(self, "max_mnt_count", "int16", "Max mount count")
        yield String(self, "magic", "string[2]", "Magic number (0x53EF)")
        if self["magic"].value != "\x53\xEF":
            raise ParserError(
                "Stream doesn't looks like EXT2/EXT3 partition "
                "(invalid magic value: %s instead of %s)" %
                (str2hex(self["magic"].value), str2hex("\x53\xEF")))
        yield Enum(self, "state", "uint16", SuperBlock.state, "File system state")
        yield Enum(self, "errors", "uint16", SuperBlock.error_handling, "Behaviour when detecting errors")
        yield Integer(self, "minor_rev_level", "uint16", "Minor revision level")
        yield Integer(self, "last_check", "uint32", "Time of last check") #  {"post": unixTimestamp}
        yield Integer(self, "check_interval", "uint32", "Maximum time between checks") #  {"post": self.postMaxTime}
        yield Enum(self, "creator_os", "uint32", SuperBlock.os_name, "Creator OS")        
        yield Integer(self, "rev_level", "uint32", "Revision level")
        yield Integer(self, "def_resuid", "uint16", "Default uid for reserved blocks")
        yield Integer(self, "def_resgid", "uint16", "Default guid for reserverd blocks")
        yield Integer(self, "first_ino", "uint32", "First non-reserved inode")
        yield Integer(self, "inode_size", "uint16", "Size of inode structure")
        if self["inode_size"].value != (68 + 15*4):
            raise ParserError(
                "EXT2/EXT3 parser error: inode of size %s are not supported" \
                % self["inode_size"].value)
        yield Integer(self, "block_group_nr", "uint16", "Block group # of this superblock")
        yield Integer(self, "feature_compat", "uint32", "Compatible feature set")
        yield Integer(self, "feature_incompat", "uint32", "Incompatible feature set")
        yield Integer(self, "feature_ro_compat", "uint32", "Read-only compatible feature set")
        yield String(self, "uuid", "string[16]", "128-bit uuid for volume")
        yield String(self, "volume_name", "string[16]", "Volume name")
        yield String(self, "last_mounted", "string[64]", "Directory where last mounted")
        yield Integer(self, "compression", "uint32", "For compression (algorithm usage bitmap)")
        yield Integer(self, "prealloc_blocks", "uint8", "Number of blocks to try to preallocate")
        yield Integer(self, "prealloc_dir_blocks", "uint8", "Number to preallocate for directories")
        yield Integer(self, "padding", "uint16", "Padding")
        yield String(self, "journal_uuid", "string[16]", "uuid of journal superblock")
        yield Integer(self, "journal_inum", "uint32", "inode number of journal file")
        yield Integer(self, "journal_dev", "uint32", "device number of journal file")
        yield Integer(self, "last_orphan", "uint32", "start of list of inodes to delete")
        yield String(self, "reserved", "string[197]", "Padding to the end of the block")

    def _getGroupCount(self):
        if self._group_count == None:
            # Calculate number of groups
            blocks_per_group = self["blocks_per_group"].value
            self._group_count = (self["blocks_count"].value - self["first_data_block"].value + (blocks_per_group - 1)) / blocks_per_group
        return self._group_count
    group_count = property(_getGroupCount)        
 
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
        self._size = self.count * self["/superblock/inode_size"].value * 8

    def createFields(self):
        for index in range(self.start, self.start+self.count):
            yield Inode(self, "inode[]", index, description="Inode %s" % index)

    def getInode(self, index):
        index = index - self.start - 1
        return self.getChunk("inode[%u]" % index).getFilter()

def testSuperblock(stream):
    oldpos = stream.tell()
    stream.seek(56*8, 1)
    magic = stream.getN(2)    
    stream.seek(oldpos)
    return (magic == "\x53\xEF")

class Group(FieldSetWithSeek):
    def __init__(self, parent, name, stream, index, description=None):
        if description == None:
            description = "Group %u" % index
        FieldSetWithSeek.__init__(self, parent, name, stream, description)
        self.index = index

# TODO: Re-enable that using event (event like "all fields are read)
#    def updateParent(self, chunk):
#        desc = "Group %s: %s" % (self.index, humanFilesize(self.getSize()))
#        if "superblock_copy" in self:
#            desc += " (with superblock copy)"
#        self.description = desc 

    def createFields(self):
        group = self["../group_desc"].getGroup(self.index)
        superblock = self["/superblock"]
        block_size = self["/"].block_size
    
        # Read block bitmap
        self.superblock_copy = False
        if testSuperblock(self.stream):
            self.superblock_copy = True
            yield SuperBlock(self, "superblock_copy", self.stream, "Superblock")
        field = self.seekField(group["block_bitmap"].value * block_size * 8)
        if field != None:
            yield field
            
        count = superblock["blocks_per_group"].value
        yield BlockBitmap(self, "block_bitmap[]", self.stream, count, 0, "Block bitmap")

        # Read inode bitmap
        assert (group["inode_bitmap"].value * block_size * 8) == self._total_field_size 
        count = superblock["inodes_per_group"].value
        yield InodeBitmap(self, "inode_bitmap[]", self.stream, count, 1, "Inode bitmap")
        addr = self._total_field_size % 4096
        if addr != 0:
            addr = self._total_field_size + (4096 - addr % 4096) * 8
            field = self.seekField(addr)
            if field != None:
                yield field
             
        count = superblock["inodes_per_group"].value
        inode_index = 1 + self.index * count
        yield InodeTable(self, "inode_table[]", self.stream, inode_index, count)

        size = (self.index+1) * superblock["blocks_per_group"].value * block_size
        if self.stream.getSize() < size:
            size = self.stream.getSize()
        assert (self._total_field_size % 8) == 0
        size = size - self._total_field_size / 8
        yield String(self, "data", "string[%u]" % size, "Data")

class EXT2_FS(FieldSetWithSeek):
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
        FieldSetWithSeek.__init__(self, parent, name, stream, description)

    def createFields(self):
        # Skip something (what is stored here? MBR?) 
        field = self.seekField(1024 * 8) 
        if field != None:
            yield field
        
        # Read superblock
        superblock = SuperBlock(self, "superblock", self.stream)
        yield superblock
        self.block_size = 1024 << superblock["log_block_size"].value # in bytes

        # Read groups' descriptor
        field = self.seekField(4096 * 8) 
        if field != None:
            yield field
        groups = GroupDescriptors(self, "group_desc", self.stream, 0, superblock.group_count)
        yield groups

        # Read groups
        address = groups.getGroup(0)["block_bitmap"].value * self.block_size * 8
        field = self.seekField(address)
        if field != None:
            yield field
        for i in range(0, superblock.group_count):
            yield Group(self, "group[]", self.stream, i)

        # Padding (?)
#        size = self.stream.getSize()*8 - self._total_field_size
#        if size != 0:
#            assert (size % 8) == 0
#            yield String(self, "end", "string[%u]" % size, "End (raw)")

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

