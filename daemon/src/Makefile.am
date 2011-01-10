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
			LinuxSessionCKFiltering.py	\
			Win32Filtering.py		\
			Win32WebContentFiltering.py	\
			Win32UsersManager.py		\
			Win32SessionFiltering.py	\
			Win32Chrono.py			\
			Win32Top.py			\
			NannyPyroBus.py			\
			etld.py	



effectivedir = $(pythondir)/nanny/daemon
effective_DATA = effective_tld_names.dat

EXTRA_DIST = effective_tld_names.dat 

if HAS_HACHOIR_REGEX
dgimporterdir = $(pythondir)/nanny/daemon
dgimporter_PYTHON = DansGuardianImporter.py
endif

