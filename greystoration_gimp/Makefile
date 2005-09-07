# Common arguments
CXXFLAGS=-Wall -O3 -ffast-math
SRC=image.cpp greycstoration.cpp dialog.cpp main.cpp

# C++ compiler
CXX=g++

# pkg-config modules needed
MODULES=gimp-2.0 gimpui-2.0 gtk+-2.0
CXXFLAGS+=$(shell pkg-config $(MODULES) --cflags)
LIBS=$(shell pkg-config $(MODULES) --libs)

# Don't use CImg interface (keyboard/mouse interaction)
CXXFLAGS+=-Dcimg_OS=-1 -Dcimg_display_type=0 

# And others variables ...
PROG=greycstoration
OBJECTS=$(patsubst %.cpp,%.o,$(SRC))
GIMPTOOL=gimptool-2.0

$(PROG): $(OBJECTS)
	@echo "Linking ..."
	@$(CXX) -o $(PROG) $(OBJECTS) $(CXXFLAGS) $(LIBS)
	
%.o: %.cpp
	@echo "Compile $@"
	@$(CXX) -c -o $@ $< $(CXXFLAGS)
	
install: $(PROG)
	$(GIMPTOOL) --install-bin $(PROG)
	
uninstall:
	$(GIMPTOOL) --uninstall-bin $(PROG)

clean:
	rm -f $(PROG) $(OBJECTS)
