BINDIR = /usr/local/bin
LIBDIR = /usr/local/share/blogtool/lib

install:
	install -m 755 *.py $(LIBDIR)
	install -m 755 bt $(BINDIR)

