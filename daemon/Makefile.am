SUBDIRS=data src

tapdir = $(datadir)/nanny/daemon
tap_DATA = nanny.tap

if NANNY_WIN32_SUPPORT
sbin_SCRIPTS = NannyService.py build_py2exe.py
endif

EXTRA_DIST=$(tap_DATA) NannyService.py build_py2exe.py 

