SUBDIRS=proxy 

corelibdir = $(pythondir)/nanny/daemon
corelib_PYTHON =	 __init__.py 			\
			Chrono.py			\
                        Daemon.py         		\
			NannyDBus.py			\
			QuarterBack.py			\
			BlockingDeferred.py		\
			FilterManager.py		\
			LinuxFiltering.py		\
			LinuxWebContentFiltering.py 	\
			LinuxUsersManager.py		\
			LinuxSessionFiltering.py	\
			LinuxSessionCKFiltering.py

if HAS_HACHOIR_REGEX
dgimporterdir = $(pythondir)/nanny/daemon
dgimporter_PYTHON = DansGuardianImporter.py
endif


INCLUDES =      -I$(top_srcdir)                 \
                $(PYTHON_CFLAGS) $(GLIB_CFLAGS)

pkgpyexec_LTLIBRARIES = gregex.la

gregex_la_SOURCES = gregexmodule.c
gregex_la_LDFLAGS =  -module -avoid-version -export-symbols-regex initgregex
gregex_la_LIBADD = $(PYTHON_LIBS) $(GLIB_LIBS)

