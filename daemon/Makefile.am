SUBDIRS=data src

tapdir = $(datadir)/nanny/daemon
tap_DATA = nanny.tap

if NANNY_WIN32_SUPPORT
sbin_SCRIPTS = nanny-daemon-win.py
endif

EXTRA_DIST=$(tap_DATA) nanny-daemon-win.py

