bin_PROGRAMS = greycstoration

bindir = $(GIMP_LIBDIR)/plug-ins

greycstoration_SOURCES = \
	plugin-intl.h \
	CImg.h \
	dialog.h \
	dialog.cpp \
	greycstoration.h \
	greycstoration.cpp \
	image.h \
	image.cpp \
	main.cpp

AM_CPPFLAGS = \
	-Dcimg_OS=-1 \
	-Dcimg_display_type=0 \
	-DLOCALEDIR=\""$(LOCALEDIR)"\"

INCLUDES = \
	-I$(top_srcdir) \
	@GIMP_CFLAGS@ \
	-I$(includedir)

LDADD = $(GIMP_LIBS)
