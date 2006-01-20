"""
EXT2 (Linux) file system parser.

Sources:
- EXT2FS source code
  http://ext2fsd.sourceforge.net/
- Analysis of the Ext2fs structure
  http://www.nondot.org/sabre/os/files/FileSystems/ext2fs/
"""

from text_handler import unixTimestamp
from chunk import EnumChunk, FormatChunk
from filter import OnDemandFilter
from plugin import registerPlugin
from tools import humanDuration, getUnixRWX, humanFilesize

class DirectoryEntry(OnDemandFilter):
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
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "dir", "EXT2 directory entry", stream, parent, "<")
        self.read("inode", "Inode", (FormatChunk, "uint32"))
        self.read("rec_len", "Record length", (FormatChunk, "uint16"))
        name_length = self.doRead("name_len", "B", "Name length", (FormatChunk, "uint8")).value
        self.read("file_type", "File type", (EnumChunk, "uint8", DirectoryEntry.file_type))
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

class Inode(OnDemandFilter):
    name = {
        1: "list of bad blocks",
        2: "Root directory",
        3: "ACL inode",
        4: "ACL inode",
        5: "Boot loader",
        6: "Undelete directory",
        8: "EXT3 journal"
    }
    
    def __init__(self, stream, parent, index):
        OnDemandFilter.__init__(self, "inode", "EXT2 inode", stream, parent, "<")
        self.index = index
        self.read("mode", "Mode", (FormatChunk, "uint16"), {"post": self.postMode})
        self.read("uid", "User ID", (FormatChunk, "uint16"))
        self.read("size", "File size", (FormatChunk, "uint32"))
        self.read("atime", "Last access time", (FormatChunk, "uint32"), {"post": unixTimestamp})
        self.read("ctime", "Creation time", (FormatChunk, "uint32"), {"post": unixTimestamp})
        self.read("mtime", "Last modification time", (FormatChunk, "uint32"), {"post": unixTimestamp})
        self.read("dtime", "Delete time", (FormatChunk, "uint32"), {"post": unixTimestamp})
        self.read("gid", "Group ID", (FormatChunk, "uint16"))
        self.read("links_count", "Links count", (FormatChunk, "uint16"))
        self.read("blocks", "Number of blocks", (FormatChunk, "uint32"))
        self.read("flags", "Flags", (FormatChunk, "uint32"))
        self.read("reserved1", "Reserved", (FormatChunk, "uint32"))
        for i in range(0,15):
            self.read("block[]", "Block %i" % i, (FormatChunk, "uint32"))
        self.read("version", "Version", (FormatChunk, "uint32"))
        self.read("file_acl", "File ACL", (FormatChunk, "uint32"))
        self.read("dir_acl", "Directory ACL", (FormatChunk, "uint32"))
        self.read("faddr", "Block where the fragment of the file resides", (FormatChunk, "uint32"))
        os = parent.getParent().getParent().superblock["creator_os"]
        if os == SuperBlock.OS_LINUX:
            self.read("frag", "Number of fragments in the block", (FormatChunk, "uint8"))
            self.read("fsize", "Fragment size", (FormatChunk, "uint8"))
            self.read("padding", "Padding", (FormatChunk, "uint16"))
            self.read("uid_high", "High 16 bits of user ID", (FormatChunk, "uint16"))
            self.read("gid_high", "High 16 bits of group ID", (FormatChunk, "uint16"))
            self.read("reserved", "Reserved", (FormatChunk, "uint32"))
        elif os == SuperBlock.OS_HURD:
            self.read("frag", "Number of fragments in the block", (FormatChunk, "uint8"))
            self.read("fsize", "Fragment size", (FormatChunk, "uint8"))
            self.read("mode_high", "High 16 bits of mode", (FormatChunk, "uint16"))
            self.read("uid_high", "High 16 bits of user ID", (FormatChunk, "uint16"))
            self.read("gid_high", "High 16 bits of group ID", (FormatChunk, "uint16"))
            self.read("author", "Author ID (?)", (FormatChunk, "uint32"))
        else:
            self.read("raw", "Reserved", (FormatChunk, "string[12]"))

    @staticmethod
    def getStaticSize(stream, args):
        return 68 + 15*4

    def updateParent(self, chunk):
        desc = "Inode %s: " % self.index
        size = humanFilesize(self["size"])
        if 11 <= self.index:
            desc = desc + "file, size=%s, mode=%s" % (size, self.getChunk("mode").display)
        else:
            if self.index in Inode.name:
                desc = desc + Inode.name[self.index]
                if self.index == 2:
                    desc = desc + " (%s)" % getUnixRWX(self["mode"])
            else:
                desc = desc + "special"
            if size == 0:
                desc = desc + " (unused)"
        chunk.description = desc
        self.setDescription(desc)

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

class Bitmap(OnDemandFilter):
    def __init__(self, stream, parent, description, count, start):
        OnDemandFilter.__init__(self, "bitmap", "%s: %s items" % (description, count), stream, parent)
        self.start = start
        size = count / 8
        self.read("block_bitmap", "Bitmap", (FormatChunk, "string[%u]" % size))

    def showFree(self, type="Block"):
        data = self["block_bitmap"]
        cpt = self.start
        for octet in data:
            octet = ord(octet)
            mask = 1
            for i in range(0,8):
                if octet & mask == 0:
                    print "%s %s free." % (type, cpt)
                cpt = cpt + 1
                mask = mask << 1

BlockBitmap = Bitmap
InodeBitmap = Bitmap

class GroupDescriptor(OnDemandFilter):
    def __init__(self, stream, parent, index):
        OnDemandFilter.__init__(self, "group", "Group descriptor", stream, parent, "<")
        self.index = index
        self.read("block_bitmap", "Points to the blocks bitmap block", (FormatChunk, "uint32"))
        self.read("inode_bitmap", "Points to the inodes bitmap block", (FormatChunk, "uint32"))
        self.read("inode_table", "Points to the inodes table first block", (FormatChunk, "uint32"))
        self.read("free_blocks_count", "Number of free blocks", (FormatChunk, "uint16"))
        self.read("free_inodes_count", "Number of free inodes", (FormatChunk, "uint16"))
        self.read("used_dirs_count", "Number of inodes allocated to directories", (FormatChunk, "uint16"))
        self.read("padding", "Padding", (FormatChunk, "uint16"))
        self.read("reserved", "Reserved", (FormatChunk, "string[12]"))

    @staticmethod
    def getStaticSize(stream, args):
        return 32

    def updateParent(self, chunk):
        superblock = self.getParent().getParent().superblock
        blocks_per_group = superblock["blocks_per_group"]
        start = self.index * blocks_per_group
        end = start + blocks_per_group 
        chunk.description = "Group descriptor: blocks %s-%s" % (start, end)
    
class SuperBlock(OnDemandFilter):
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
   
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "super_block", "Super block", stream, parent, "<")
        self.read("inodes_count", "Inodes count", (FormatChunk, "uint32"))
        self.read("blocks_count", "Blocks count", (FormatChunk, "uint32"))
        self.read("r_blocks_count", "Reserved blocks count", (FormatChunk, "uint32"))
        self.read("free_blocks_count", "Free blocks count", (FormatChunk, "uint32"))
        self.read("free_inodes_count", "Free inodes count", (FormatChunk, "uint32"))
        self.read("first_data_block", "First data block", (FormatChunk, "uint32"))
        assert self["first_data_block"] == 0
        self.read("log_block_size", "Block size", (FormatChunk, "uint32"))
        self.read("log_frag_size", "Fragment size", (FormatChunk, "uint32"))
        self.read("blocks_per_group", "Blocks per group", (FormatChunk, "uint32"))
        self.read("frags_per_group", "Fragments per group", (FormatChunk, "uint32"))
        self.read("inodes_per_group", "Inodes per group", (FormatChunk, "uint32"))
        self.read("mtime", "Mount time", (FormatChunk, "uint32"), {"post": unixTimestamp})
        self.read("wtime", "Write time", (FormatChunk, "uint32"), {"post": unixTimestamp})
        self.read("mnt_count", "Mount count", (FormatChunk, "uint16"))
        self.read("max_mnt_count", "Max mount count", (FormatChunk, "int16"))
        self.read("magic", "Magic number (0x53EF)", (FormatChunk, "string[2]"))
        assert self["magic"] == "\x53\xEF"
        self.read("state", "File system state", (EnumChunk, "uint16", SuperBlock.state))
        self.read("errors", "Behaviour when detecting errors", (EnumChunk, "uint16", SuperBlock.error_handling))
        self.read("minor_rev_level", "Minor revision level", (FormatChunk, "uint16"))
        self.read("last_check", "Time of last check", (FormatChunk, "uint32"), {"post": unixTimestamp})
        self.read("check_interval", "Maximum time between checks", (FormatChunk, "uint32"), {"post": self.postMaxTime})        
        self.read("creator_os", "Creator OS", (EnumChunk, "uint32", SuperBlock.os_name))        
        self.read("rev_level", "Revision level", (FormatChunk, "uint32"))
        self.read("def_resuid", "Default uid for reserved blocks", (FormatChunk, "uint16"))
        self.read("def_resgid", "Default guid for reserverd blocks", (FormatChunk, "uint16"))
        self.read("first_ino", "First non-reserved inode", (FormatChunk, "uint32"))
        self.read("inode_size", "Size of inode structure", (FormatChunk, "uint16"))
        assert self["inode_size"] == (68 + 15*4)
        self.read("block_group_nr", "Block group # of this superblock", (FormatChunk, "uint16"))
        self.read("feature_compat", "Compatible feature set", (FormatChunk, "uint32"))
        self.read("feature_incompat", "Incompatible feature set", (FormatChunk, "uint32"))
        self.read("feature_ro_compat", "Read-only compatible feature set", (FormatChunk, "uint32"))
        self.read("uuid", "128-bit uuid for volume", (FormatChunk, "string[16]"))
        self.read("volume_name", "Volume name", (FormatChunk, "string[16]"))
        self.read("last_mounted", "Directory where last mounted", (FormatChunk, "string[64]"))
        self.read("compression", "For compression (algorithm usage bitmap)", (FormatChunk, "uint32"))
        self.read("prealloc_blocks", "Number of blocks to try to preallocate", (FormatChunk, "uint8"))
        self.read("prealloc_dir_blocks", "Number to preallocate for directories", (FormatChunk, "uint8"))
        self.read("padding", "Padding", (FormatChunk, "uint16"))
        self.read("journal_uuid", "uuid of journal superblock", (FormatChunk, "string[16]"))
        self.read("journal_inum", "inode number of journal file", (FormatChunk, "uint32"))
        self.read("journal_dev", "device number of journal file", (FormatChunk, "uint32"))
        self.read("last_orphan", "start of list of inodes to delete", (FormatChunk, "uint32"))
        self.read("reserved", "Padding to the end of the block", (FormatChunk, "string[197]"))

        # Calculate number of groups
        blocks_per_group = self["blocks_per_group"]
        self.group_count = (self["blocks_count"] - self["first_data_block"] + (blocks_per_group - 1)) / blocks_per_group

    @staticmethod
    def getStaticSize(stream, args):
        return 433
 
    def updateParent(self, chunk):
        if self["feature_compat"] & 4 == 4:
            type = "ext3"
        else:
            type = "ext2"
        desc = "Superblock: %s file system" % type
        self.setDescription(desc)
        chunk.description = desc

    def postMaxTime(self, chunk):
        return humanDuration(chunk.value * 1000)

class GroupDescriptors(OnDemandFilter):
    def __init__(self, stream, parent, count, start):
        OnDemandFilter.__init__(self, "groups", "Group descriptors: %s items" % count, stream, parent)
        self.start = start
        for i in range(0, count):
            self.read("group[]", "Group", (GroupDescriptor, i))

    def getGroup(self, index):
        return self["group[%s]" % (self.start + index)]

class InodeTable(OnDemandFilter):
    def __init__(self, stream, parent, start, count):
        OnDemandFilter.__init__(self, "ino_table", "Inode table: %s inodes" % count, stream, parent)
        self.start = start
        for index in range(self.start, self.start+count):
            self.read("inode[]", "Inode %s" % index, (Inode, index))

    def __getitem__(self, index):
        index = index - self.start - 1
        return self.getChunk("inode[%u]" % index).getFilter()

def testSuperblock(stream):
    oldpos = stream.tell()
    stream.seek(56, 1)
    magic = stream.getN(2)    
    stream.seek(oldpos)
    return (magic == "\x53\xEF")

class Group(OnDemandFilter):
    def __init__(self, stream, parent, index):
        OnDemandFilter.__init__(self, "group", "Group %u" % index, stream, parent)
        self.index = index
        group = parent["group_desc"].getGroup(index)
        superblock = parent.superblock
        block_size = parent.block_size
    
        # Read block bitmap
        self.superblock_copy = False
        if testSuperblock(stream):
            self.read("superblock_copy", "Superblock", (SuperBlock,))
            self.superblock_copy = True
        self.seek(group["block_bitmap"] * block_size)
            
        count = superblock["blocks_per_group"]
        self.read("block_bitmap[]", "Block bitmap", (BlockBitmap, "Block bitmap", count, 0), {"size": count / 8})

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

class EXT2_FS(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "ext2", "EXT2 file system", stream, parent)
        
        # Read superblock
        self.seek(1024) 
        self.superblock = self.doRead("superblock", "Super block", (SuperBlock,))
        self.block_size = 1024 << self.superblock["log_block_size"]

        # Read groups
        self.seek(4096) 
        groups = self.doRead("group_desc", "Group descriptors", (GroupDescriptors, self.superblock.group_count, 0))
        self.seek(groups.getGroup(0)["block_bitmap"] * self.block_size)
        for i in range(0,self.superblock.group_count):
            self.read("group[]", "Group", (Group, i))

        size = stream.getSize() - stream.tell()
        if size != 0:
            self.read("end", "End (raw)", (FormatChunk, "string[%u]" % size))

    def seek(self, to):
        size = to - self.getStream().tell()
        assert 0 <= size
        if 0 < size:
            self.read("raw[]", "Raw", (FormatChunk, "string[%u]" % size))

    def readDirectory(self, inode):
        stream = self.getStream()
        block_index = 0
        while True:
            assert block_index < 12
            block = inode["block[%u]" % block_index]
            if block == 0:
                return
            self.seek(block * self.block_size)

            total = 0
            while total < self.block_size:
                entry = self.doRead("directory[]", "Directory entry", (DirectoryEntry,))
                if entry["inode"] == 0:
                    return
                total = total + entry.getSize()
            assert total == self.block_size
            block_index = block_index + 1

registerPlugin(EXT2_FS, "hachoir/fs-ext2")
