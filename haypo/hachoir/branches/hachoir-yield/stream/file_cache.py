from cache import Cache

class FileCacheEntry:
    def __init__(self, index, data):
        self.index = index
        self.data = data
        self.used = 0

    def __cmp__(self, to):
        return cmp(self.used, to.used)

class FileCache(Cache):
    def __init__(self, file, file_size, block_size=4096, block_count=100):
        Cache.__init__(self, "FileCache")
        self.file = file
        self.file_size = file_size
        self.block_size = block_size
        self.max_block = block_count
        self.blocks = {}

    def getCacheSize(self):
        return len(self.blocks)

    def purgeCache(self):
        self.blocks = {}

    def removeOldestBlock(self):
        entry = min(self.blocks.values())
        del self.blocks[entry.index]

    def read(self, position, length):
        block_position = position % self.block_size
        block_index = position / self.block_size
        length_copy = length
        assert position+length <= self.file_size
        
        data = ""
        while 0 < length:
            if block_index not in self.blocks:
                if self.max_block <= len(self.blocks):
                    self.removeOldestBlock()
                self.file.seek(block_index * self.block_size)
                block_data = self.file.read(self.block_size)
                assert (len(block_data) == self.block_size) or self.file.tell() == self.file_size
                self.blocks[block_index] = FileCacheEntry(block_index, block_data)
            else:
                block_data = self.blocks[block_index].data
            self.blocks[block_index].used = self.blocks[block_index].used + 1
            if block_position != 0 or length != self.block_size:
                end = block_position+length
                if self.block_size < end:
                    end = self.block_size
                block_data = block_data[block_position:end]
            data = data + block_data
            block_position = 0
            block_index = block_index + 1
            length = length - len(block_data)
        assert len(data) == length_copy
        return data

