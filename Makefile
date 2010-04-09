BINDIR = /usr/local/bin
LIBDIR = /usr/local/share/blogtool/lib

install:
	-mkdir -p $(LIBDIR)
	-mkdir -p $(LIBDIR)/xmlproxy

	install -m 755 *.py $(LIBDIR)
	install -m 755 bt $(BINDIR)
	install -m 755 ./xmlproxy/*.py $(LIBDIR)/xmlproxy
