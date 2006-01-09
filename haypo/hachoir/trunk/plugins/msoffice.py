"""
Microsoft Office documents parser.

Informations:
* wordole.c of AntiWord program (v0.35)
  Copyright (C) 1998-2003 A.J. van Os
  Released under GPL
  http://www.winfield.demon.nl/

Author: Victor Stinner
Creation: 8 january 2005
"""

from filter import OnDemandFilter
from chunk import FormatChunk
from plugin import registerPlugin

class BlockDepot(OnDemandFilter):
    def __init__(self, stream, parent, count):
        OnDemandFilter.__init__(self, "block_depot", "Block depot", stream, parent, "<")
        self.count = count
        assert self.count != 0
        for index in range(0, self.count):
            self.read("item[]", "", (FormatChunk, "uint32"))

    def updateParent(self, chunk):
        chunk.description = "Block depot: %s item(s)" % self.count

class BigBlockDepot(OnDemandFilter):
    def __init__(self, stream, parent, count):
        OnDemandFilter.__init__(self, "bbd", "Big block depot", stream, parent, "<")
        self.items = []
        for i in range(0, count):
            item = self.doRead("item[]", "", (FormatChunk, "uint32")).value
            self.items.append(item)

    def updateParent(self, chunk):
        chunk.description = "Big block depot: %s item(s)" % len(self.items)

class OLE_Document(OnDemandFilter):
    BIG_BLOCK_SIZE = 512
    END_OF_CHAIN = 0xfffffffe

    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "ole_doc", "OLE document", stream, parent, "<")
        self.read("id", "OLE object identifier", (FormatChunk, "string[4]"))
        assert self["id"] == "\xD0\xCF\x11\xE0"

        max_block = stream.getSize() / OLE_Document.BIG_BLOCK_SIZE - 2
        assert 2 <= max_block
        tBBDLen =  max_block + 1

        # Header
        self.seek(0x2c)
        self.read("nb_bbd_blocks", "Number of Big Block Depot blocks", (FormatChunk, "uint32"))
        root = self.doRead("root_start_block", "Root start block", (FormatChunk, "uint32")).value
        self.seek(0x3c)
        self.read("sbd_start_block", "Small Block Depot start block", (FormatChunk, "uint32"))
        self.seek(0x44)
        ulAdditionalBBDlist = self.doRead("add_bbd_list[]", "Additionnal BBD list", (FormatChunk, "uint32")).value

        # Read first bbd
        iToGo = self["nb_bbd_blocks"]
        self.seek(0x4c)
        self.bbd = []
        bbd = self.doRead("bbd[]", "Big block depot", (BigBlockDepot, min(iToGo, 109)))
        self.bbd.extend( bbd.items )
        iToGo -= 109
        start = 109

        # SBL things
#        self.seek( (root+1)*OLE_Document.BIG_BLOCK_SIZE + 0x74)
#        self.read("sbl_start_block", "SDL start block", (FormatChunk, "uint32"))
#        self.read("sbl_len", "SBL length", (FormatChunk, "uint32"))

        # Read next bbd
        while (ulAdditionalBBDlist != OLE_Document.END_OF_CHAIN and iToGo > 0):
            ulBdbListStart = (ulAdditionalBBDlist + 1) * OLE_Document.BIG_BLOCK_SIZE
            self.seek(ulBdbListStart)
            bbd = self.doRead("bbd[]", "Big block depot", (BigBlockDepot, min(iToGo, 127)))
            self.bbd.extend( bbd.items )
            ulAdditionalBBDlist = self.doRead("add_bdd_list[]", "Additionnal BDD list", (FormatChunk, "uint32")).value
            ulStart += 127;
            iToGo -= 127;

        self.bGetBBD(self.bbd, self["nb_bbd_blocks"], tBBDLen)

        self.addPadding()

    def bGetBBD(self, aulDepot, tDepotLen, count):
        index = 0
        while count != 0:
            assert index < tDepotLen
            pos = (aulDepot[index] + 1) * OLE_Document.BIG_BLOCK_SIZE;
            self.seek(pos)

            tDone = min(count, OLE_Document.BIG_BLOCK_SIZE / 4)
            assert not(tDone > count)

            self.read("block_depot[]", "Block depot", (BlockDepot, tDone))
            
            assert tDone != 0
            count -= tDone
            index += 1

    def seek(self, to):
        size = to - self.getStream().tell()
        assert 0 <= size
        if 0 < size:
            self.read("raw[]", "Raw", (FormatChunk, "string[%u]" % size))

registerPlugin(OLE_Document, "application/msword")
