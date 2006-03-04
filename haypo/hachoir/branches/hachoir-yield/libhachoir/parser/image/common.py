from field import FieldSet, Integer

class RGB(FieldSet):
    color_name = {
        0x000000: "Black",
        0xFFFFFF: "White"
    }
    static_size = 3*8
    
    def __init__(self, parent, name, stream, description=None):
        FieldSet.__init__(self, parent, name, stream, description)
        if self.description == None:
            self.description = self.getColorName()

    def createFields(self):
        yield Integer(self, "red", "uint8", "Red")
        yield Integer(self, "green", "uint8", "Green")
        yield Integer(self, "blue", "uint8", "Blue")

    def getColorName(self):
        value = (self["red"].value << 16) + (self["green"].value << 8) + self["blue"].value
        if value in RGB.color_name:
            return "RGB color: "+RGB.color_name[value]
        else:
            return "RGB color: #%02X%02X%02X" % \
                (self["red"].value, self["green"].value, self["blue"].value)

class Palette(FieldSet):
    def __init__(self, parent, name, nb_colors, description=None):
        self.nb_colors = nb_colors
        size = self.nb_colors * RGB.static_size
        if description == None:
            description = "Palette of %u RGB colors" % self.nb_colors
        FieldSet.__init__(self, parent, name, parent.stream, size=size, description=description)

    def createFields(self):
        for i in range(0, self.nb_colors):
            yield RGB(self, "color[]", self.stream)
