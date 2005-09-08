.PHONY : clean mo
POT_SOURCES=happywarry-server.py
POT_OUT=messages.gzz
what:
	@echo "Make what?"
	@echo "o pot: Generate $(POT_OUT) file (gettext)."
	@echo "o mo: Generate *.mo file (gettext)."
	@echo "o clean: Remove generated and temporary files (eg. *.pyc)"

mo:
	@$(foreach file,$(shell find -name "*.po"),echo "Compile $(file)" && msgfmt -o $(patsubst %.po,%.mo,$(file)) $(file))
	
pot: $(POT_OUT)
POT_OUT: $(POT_SOURCES)
	pygettext -o $(POT_OUT) $(POT_SOURCES)

clean:
	rm -f $(shell find -name "*.swp" -o -name "*~" -o -name "*.mo" -o -name "*.pyc")
