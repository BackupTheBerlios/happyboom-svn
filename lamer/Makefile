CC=gcc
CFLAGS=-Wall
IN=tool/src/gftp_descramble.c
OUT=tool/gftp_descramble
$(OUT): $(IN)
	$(CC) $(IN) -o $(OUT) $(CFLAGS)
exec: $(OUT)
	./$(OUT)
clean:
	rm -f $(OUT)
