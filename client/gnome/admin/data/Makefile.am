SUBDIRS=glade icons

desktopdir = $(datadir)/applications/
desktop_in_files = nanny-admin-console.desktop.in 
desktop_DATA = $(desktop_in_files:.desktop.in=.desktop)
@INTLTOOL_DESKTOP_RULE@

EXTRA_DIST=$(desktop_DATA)
