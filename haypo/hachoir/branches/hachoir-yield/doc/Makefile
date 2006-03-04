SOURCES=$(wildcard *.txt)
HTML=$(patsubst %.txt,%.html,$(SOURCES))

all: $(HTML)
	@echo "Documentation updated."

%.html: %.txt
	@echo "Compile documentation $<"
	@rst2html.py > $@ < $<

clean:
	@echo "Clean (remove *.html)"
	@rm -f $(HTML)
