"""
EXT2 (Linux) file system parser.

Sources:
- EXT2FS source code -> http://ext2fsd.sourceforge.net/
"""

from datetime import datetime
from filter import Filter
from plugin import registerPlugin
from tools import humanDuration

class EXT2_SuperBlock(Filter):
    error_handling = {
        1: "Continue"
    }
    os_name = {
        0: "Linux",
        1: "Hurd",
        2: "Masix",
        3: "FreeBSD",
        4: "Lites",
        5: "WinNT"
    }
    
    def __init__(self, stream, parent):
        Filter.__init__(self, "ext2", "EXT2 file system", stream, parent)
        self.read("inodes_count", "<L", "Inodes count")
        self.read("blocks_count", "<L", "Blocks count")
        self.read("r_blocks_count", "<L", "Reserved blocks count")
        self.read("free_blocks_count", "<L", "Free blocks count")
        self.read("free_inodes_count", "<L", "Free inodes count")
        self.read("first_data_block", "<L", "First data block")
        self.read("log_block_size", "<L", "Block size")
        self.read("log_frag_size", "<L", "Fragment size")
        self.read("blocks_per_group", "<L", "Blocks per group")
        self.read("frags_per_group", "<L", "Fragments per group")
        self.read("inodes_per_group", "<L", "Inodes per group")
        self.read("mtime", "<L", "Mount time", post=self.getTime)
        self.read("wtime", "<L", "Write time", post=self.getTime)
        self.read("mnt_count", "<H", "Mount count")
        self.read("max_mnt_count", "<h", "Max mount count")
        id = self.read("magic", ">H", "Magic number (0x53EF)").value
        assert id == 0x53EF

        self.read("state", "<H", "File system state")

        # Read error handling
        chunk = self.read("errors", "<H", "")
        desc = "Behaviour when detecting errors"
        if chunk.value in EXT2_SuperBlock.error_handling:
            desc = "%s: %s" % (desc, EXT2_SuperBlock.error_handling[chunk.value])
        chunk.description = desc
        
        self.read("minor_rev_level", "<H", "Minor revision level")
        self.read("last_check", "<L", "Time of last check", post=self.getTime)
        self.read("check_interval", "<L", "Maximum time between checks", post=self.postMaxTime)
        
        chunk = self.read("creator_os", "<L", "")
        desc = "Creator OS"
        if chunk.value in EXT2_SuperBlock.os_name:
            desc = "%s: %s" % (desc, EXT2_SuperBlock.os_name[chunk.value])
        chunk.description = desc
        
        self.read("rev_level", "<L", "Revision level")
        self.read("def_resuid", "<H", "Default uid for reserved blocks")
        self.read("def_resgid", "<H", "Default guid for reserverd blocks")

        # ---------

        self.read("first_ino", "<L", "First non-reserved inode")
        self.read("inode_size", "<H", "Size of inode structure")
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

class EXT2_FS(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "ext2", "EXT2 file system", stream, parent)
        self.read("raw[]", "1024s", "Raw data")
        self.readChild("superblock", EXT2_SuperBlock)

registerPlugin(EXT2_FS, "hachoir/fs-ext2")
