"""
EXT2 (Linux) file system parser.

Sources:
- EXT2FS source code
  http://ext2fsd.sourceforge.net/
- Analysis of the Ext2fs structure
  http://www.nondot.org/sabre/os/files/FileSystems/ext2fs/
"""

from datetime import datetime
from filter import Filter, OnlyFormatChunksFilter, OnlyFiltersFilter
from plugin import registerPlugin
from tools import humanDuration, getUnixRWX 

class DirectoryEntry(OnlyFormatChunksFilter):
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
        OnlyFormatChunksFilter.__init__(self, "dir", "EXT2 directory entry", stream, parent)
        self.read("inode", "<L", "Inode")
        self.read("rec_len", "<H", "Record length")
        name_length = self.doRead("name_len", "B", "Name length").value
        self.read("file_type", "B", "File type", post=self.postFileType)
        self.read("name", "%us" % name_length, "Name")
        size = self["rec_len"]-8-name_length 
        if size != 0:
            self.read("padding", "%us" % size, "Padding")

    def updateParent(self, chunk):        
        name = self["name"].strip("\0")
        if name != "":
            desc = "Directory entry: %s" % name
        else:
            desc = "Directory entry (empty)"
        chunk.description = desc
        self.setDescription(desc)

    def postFileType(self, chunk):
        type = chunk.value
        return DirectoryEntry.file_type.get(type, "Unknow (%02X)" % type)

class Inode(OnlyFormatChunksFilter):
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
        OnlyFormatChunksFilter.__init__(self, "inode", "EXT2 inode", stream, parent)
        self.index = index
        self.read("mode", "<H", "Mode", post=self.postMode)
        self.read("uid", "<H", "User ID")
        self.read("size", "<L", "File size")
        self.read("atime", "<L", "Last access time", post=self.getTime)
        self.read("ctime", "<L", "Creation time", post=self.getTime)
        self.read("mtime", "<L", "Last modification time", post=self.getTime)
        self.read("dtime", "<L", "Delete time", post=self.getTime)
        self.read("gid", "<H", "Group ID")
        self.read("links_count", "<H", "Links count")
        self.read("blocks", "<L", "Number of blocks")
        self.read("flags", "<L", "Flags")
        self.read("reserved1", "<L", "Reserved")
        for i in range(0,15):
            self.read("block[]", "<L", "Block %i" % i)
        self.read("version", "<L", "Version")
        self.read("file_acl", "<L", "File ACL")
        self.read("dir_acl", "<L", "Directory ACL")
        self.read("faddr", "<L", "Block where the fragment of the file resides")
        os = parent.getParent().superblock["creator_os"]
        if os == SuperBlock.OS_LINUX:
            self.read("frag", "B", "Number of fragments in the block")
            self.read("fsize", "B", "Fragment size")
            self.read("padding", "<H", "Padding")
            self.read("uid_high", "<H", "High 16 bits of user ID")
            self.read("gid_high", "<H", "High 16 bits of group ID")
            self.read("reserved", "<L", "Reserved")
        elif os == SuperBlock.OS_HURD:
            self.read("frag", "B", "Number of fragments in the block")
            self.read("fsize", "B", "Fragment size")
            self.read("mode_high", "<H", "High 16 bits of mode")
            self.read("uid_high", "<H", "High 16 bits of user ID")
            self.read("gid_high", "<H", "High 16 bits of group ID")
            self.read("author", "<L", "Author ID (?)")
        else:
            self.read("raw", "12s", "Reserved")

    def updateParent(self, chunk):
        desc = "Inode %s: " % self.index
        size = self["size"]
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

    def getTime(self, chunk):
        if chunk.value != 0:
            return datetime.fromtimestamp(chunk.value)
        else:
            return "(empty)"

class Bitmap(OnlyFormatChunksFilter):
    def __init__(self, stream, parent, size, start):
        OnlyFormatChunksFilter.__init__(self, "group", "EXT2 group", stream, parent)
        self.start = start
        self.read("block_bitmap", "%us" % size, "Bitmap")

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

class EXT2_Group(OnlyFormatChunksFilter):
    def __init__(self, stream, parent):
        OnlyFormatChunksFilter.__init__(self, "group", "EXT2 group", stream, parent)
        self.read("block_bitmap", "<L", "Points to the blocks bitmap block")
        self.read("inode_bitmap", "<L", "Points to the inodes bitmap block")
        self.read("inode_table", "<L", "Points to the inodes table first block")
        self.read("free_blocks_count", "<H", "Number of free blocks")
        self.read("free_inodes_count", "<H", "Number of free inodes")
        self.read("used_dirs_count", "<H", "Number of inodes allocated to directories")
        self.read("padding", "<H", "Padding")
        self.read("reserved", "12s", "Reserved")

class SuperBlock(OnlyFormatChunksFilter):
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
        OnlyFormatChunksFilter.__init__(self, "super_block", "EXT2 super block", stream, parent)
        self.read("inodes_count", "<L", "Inodes count")
        self.read("blocks_count", "<L", "Blocks count")
        self.read("r_blocks_count", "<L", "Reserved blocks count")
        self.read("free_blocks_count", "<L", "Free blocks count")
        self.read("free_inodes_count", "<L", "Free inodes count")
        first = self.doRead("first_data_block", "<L", "First data block").value
        assert (first == 0)
        self.read("log_block_size", "<L", "Block size")
        self.read("log_frag_size", "<L", "Fragment size")
        self.read("blocks_per_group", "<L", "Blocks per group")
        self.read("frags_per_group", "<L", "Fragments per group")
        self.read("inodes_per_group", "<L", "Inodes per group")
        self.read("mtime", "<L", "Mount time", post=self.getTime)
        self.read("wtime", "<L", "Write time", post=self.getTime)
        self.read("mnt_count", "<H", "Mount count")
        self.read("max_mnt_count", "<h", "Max mount count")
        id = self.doRead("magic", ">H", "Magic number (0x53EF)").value
        assert id == 0x53EF

        # Read state
        chunk = self.doRead("state", "<H", "File system state")
        chunk.description = "Behaviour when detecting errors: %s" % \
            SuperBlock.state.get(chunk.value, "Unknow (%s)" % chunk.value)

        # Read error handling
        chunk = self.doRead("errors", "<H", "")
        desc = "Behaviour when detecting errors"
        if chunk.value in SuperBlock.error_handling:
            desc = "%s: %s" % (desc, SuperBlock.error_handling[chunk.value])
        chunk.description = desc
        
        self.read("minor_rev_level", "<H", "Minor revision level")
        self.read("last_check", "<L", "Time of last check", post=self.getTime)
        self.read("check_interval", "<L", "Maximum time between checks", post=self.postMaxTime)
        
        chunk = self.doRead("creator_os", "<L", "")
        desc = "Creator OS"
        if chunk.value in SuperBlock.os_name:
            desc = "%s: %s" % (desc, SuperBlock.os_name[chunk.value])
        chunk.description = desc
        
        self.read("rev_level", "<L", "Revision level")
        self.read("def_resuid", "<H", "Default uid for reserved blocks")
        self.read("def_resgid", "<H", "Default guid for reserverd blocks")

        # ---------

        self.read("first_ino", "<L", "First non-reserved inode")
        inode_size = self.doRead("inode_size", "<H", "Size of inode structure").value
        assert inode_size == (68 + 15*4)
        self.read("block_group_nr", "<H", "Block group # of this superblock")
        self.read("feature_compat", "<L", "Compatible feature set")
        self.read("feature_incompat", "<L", "Incompatible feature set")
        self.read("feature_ro_compat", "<L", "Read-only compatible feature set")
        self.read("uuid", "16s", "128-bit uuid for volume")
        self.read("volume_name", "16s", "Volume name")
        self.read("last_mounted", "64s", "Directory where last mounted")
        self.read("compression", "<L", "For compression (algorithm usage bitmap)")
        
        self.read("prealloc_blocks", "B", "Number of blocks to try to preallocate")
        self.read("prealloc_dir_blocks", "B", "Number to preallocate for directories")
        self.read("padding", "H", "Padding")
        
        self.read("journal_uuid", "16s", "uuid of journal superblock")
        self.read("journal_inum", "<L", "inode number of journal file")
        self.read("journal_dev", "<L", "device number of journal file")
        self.read("last_orphan", "<L", "start of list of inodes to delete")
        
        self.read("reserved", "197s", "Padding to the end of the block")

        blocks_per_group = self["blocks_per_group"]
        self.group_count = (self["blocks_count"] - self["first_data_block"] + blocks_per_group - 1) / blocks_per_group

    def updateParent(self, chunk):
        if self["feature_compat"] & 4 == 4:
            type = "ext3"
        else:
            type = "ext2"
        desc = "EXT2 Superblock: %s file system" % type
        self.setDescription(desc)
        chunk.description = desc

    def postMaxTime(self, chunk):
        return humanDuration(chunk.value * 1000)

    def getTime(self, chunk):
        return datetime.fromtimestamp(chunk.value)

class Groups(OnlyFormatChunksFilter):
    def __init__(self, stream, parent, count):
        OnlyFormatChunksFilter.__init__(self, "groups", "EXT2 groups", stream, parent)
        self.items = []
        for i in range(0, count):
            group = self.doReadChild("group[]", "Group", EXT2_Group).getFilter()
            self.items.append(group)

    def __getitem__(self, index):
        return self.items[index]

class InodeTable(OnlyFormatChunksFilter):
    def __init__(self, stream, parent, start, count):
        OnlyFormatChunksFilter.__init__(self, "ino_table", "EXT2 inode table", stream, parent)
        self.inodes = {}
        self.start = start
        chunk_size = parent.superblock["inode_size"]
        for index in range(self.start, self.start+count):
            self.readSizedChild("inode[]", "Inode %s" % index, chunk_size, Inode, index)

    def __getitem__(self, index):
        index = index - self.start - 1
        return self.getChunk("inode[%u]" % index).getFilter()

#class Directory(Filter):
#    def __init__(self, stream, parent):
#        Filter.__init__(self, "dir", "EXT2 directory", stream, parent)
#        self.read("inode", "<L", "Inode")

class EXT2_FS(OnlyFormatChunksFilter):
    def __init__(self, stream, parent):
        OnlyFormatChunksFilter.__init__(self, "ext2", "EXT2 file system", stream, parent)
        
        # Read superblock
        self.seek(1024) 
        self.superblock = self.doReadChild("superblock", "Super block", SuperBlock).getFilter()
        self.block_size = 1024 << self.superblock["log_block_size"]

        # Read groups
        self.seek(4096) 
        groups = self.doReadChild("groups", "Groups", Groups, self.superblock.group_count).getFilter()
        inode_index = 1
        for i in range(0,2):
            group = groups[i]
        
            # Read block bitmap
            self.seek(group["block_bitmap"] * self.block_size)
            count = self.superblock["blocks_per_group"]
            self.readSizedChild("block_bitmap[]", "Block bitmap", count / 8, BlockBitmap, count / 8, 0)

            # Read inode bitmap
            assert (group["inode_bitmap"] * self.block_size) == stream.tell()
            count = self.superblock["inodes_per_group"]
            self.readSizedChild("inode_bitmap[]", "Inode bitmap", count / 8, InodeBitmap, count / 8, 1)
            addr = stream.tell() % 4096
            if addr != 0:
                addr = stream.tell() + (4096 - addr % 4096)
                self.seek(addr)
                 
            count = self.superblock["inodes_per_group"]
            inode_table = self.readChild("inode_table[]", "Inode table", InodeTable, inode_index, count)
            inode_index += count
            return
            if i == 0:
                root = self[inode_table][2]
                self.readDirectory(root)

        size = stream.getSize() - stream.tell()
        self.read("end", "%us" % size, "End (raw)")

    def seek(self, to):
        size = to - self.getStream().tell()
        assert 0 <= size
        if 0 < size:
            self.read("raw[]", "%us" % size, "Raw")

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
                entry = self.doReadChild("directory[]", "Directory entry", DirectoryEntry).getFilter()
                if entry["inode"] == 0:
                    return
                total = total + entry.getSize()
            assert total == self.block_size
            block_index = block_index + 1

registerPlugin(EXT2_FS, "hachoir/fs-ext2")
