AC_INIT(README)

PACKAGE=nanny
VERSION=2.29.1

AC_SUBST(PACKAGE)
AC_SUBST(VERSION)

AM_INIT_AUTOMAKE($PACKAGE, $VERSION)
AM_CONFIG_HEADER(config.h)
AC_CONFIG_MACRO_DIR([m4])

AM_MAINTAINER_MODE

AC_ISC_POSIX
AC_PROG_CC
AC_STDC_HEADERS
AM_DISABLE_STATIC
AC_PROG_LIBTOOL

AC_ARG_WITH(init-scripts,
  [  --with-init-scripts=[redhat/debian/suse/None]  Install init.d scripts [default=None]],,
  with_init_scripts=None)

GNOME_DOC_INIT

dnl check for python
dnl ----------------------------
AM_PATH_PYTHON

PKG_CHECK_MODULES(PYGTK, pygtk-2.0 >= 2.6)
AC_SUBST(PYGTK_CFLAGS)
AC_SUBST(PYGTK_LIBS)


PKG_CHECK_MODULES(PYDBUS, dbus-python >= 0.80)
AC_SUBST(PYDBUS_CFLAGS)
AC_SUBST(PYDBUS_LIBS)

dnl check for glib
dnl -----------------------------
GLIB_REQUIRED=2.12.0

PKG_CHECK_MODULES(GLIB, glib-2.0 >= $GLIB_REQUIRED gobject-2.0 >= $GLIB_REQUIRED)

AC_SUBST(GLIB_CFLAGS)
AC_SUBST(GLIB_LIBS)

dnl check for python headers
dnl ------------------------------
AC_MSG_CHECKING(for shared library Python stuff)

PY_PREFIX=`$PYTHON -c 'import sys ; print sys.prefix'`
PY_EXEC_PREFIX=`$PYTHON -c 'import sys ; print sys.exec_prefix'`
PYTHON_LIBS="-lpython$PYTHON_VERSION"
PYTHON_LIB_LOC="-L$PY_EXEC_PREFIX/lib/python$PYTHON_VERSION/config"
PYTHON_CFLAGS="-I$PY_PREFIX/include/python$PYTHON_VERSION"
PYTHON_MAKEFILE="$PY_EXEC_PREFIX/lib/python$PYTHON_VERSION/config/Makefile"
PYTHON_LOCALMODLIBS=`sed -n -e 's/^LOCALMODLIBS=\(.*\)/\1/p' $PYTHON_MAKEFILE`
PYTHON_BASEMODLIBS=`sed -n -e 's/^BASEMODLIBS=\(.*\)/\1/p' $PYTHON_MAKEFILE`
PYTHON_OTHER_LIBS=`sed -n -e 's/^LIBS=\(.*\)/\1/p' $PYTHON_MAKEFILE`
PYTHON_EXTRA_LIBS="$PYTHON_LOCALMODLIBS $PYTHON_BASEMODLIBS $PYTHON_OTHER_LIBS"
AC_SUBST([PYTHON_LIBS])
AC_SUBST([PYTHON_LIB_LOC])
AC_SUBST([PYTHON_CFLAGS])
AC_SUBST([PYTHON_EXTRA_LIBS])

dnl check for twisted.web
dnl -----------------------------------------
AC_MSG_CHECKING(for twisted.web)
prog="
import sys
try:
  import twisted.web
except RuntimeError:
  sys.exit(0)
except ImportError:
  sys.exit(1)
sys.exit(0)
"

if $PYTHON -c "$prog" 1>&AC_FD_CC 2>&AC_FD_CC
then
  AC_MSG_RESULT(found)
else
  AC_MSG_RESULT(not found)
  AC_MSG_ERROR([You need to have twisted.web installed])
fi

dnl check for python-imaging
dnl -----------------------------------------
AC_MSG_CHECKING(for python-imaging)
prog="
import sys
try:
  import Image
except RuntimeError:
  sys.exit(0)
except ImportError:
  sys.exit(1)
sys.exit(0)
"
   
if $PYTHON -c "$prog" 1>&AC_FD_CC 2>&AC_FD_CC
then
  AC_MSG_RESULT(found)
else
  AC_MSG_RESULT(not found)
  AC_MSG_ERROR([You need to have python-imaging installed])
fi

dnl check for python-hachoir-regex
dnl -----------------------------------------
AC_MSG_CHECKING(for python-hachoir-regex)
prog="
import sys
try:
  from hachoir_regex import parse, createRange, createString
except RuntimeError:
  sys.exit(0)
except ImportError:
  sys.exit(1)
sys.exit(0)
"
   
if $PYTHON -c "$prog" 1>&AC_FD_CC 2>&AC_FD_CC
then
  AC_MSG_RESULT(found)
else
  AC_MSG_RESULT(not found)
  AC_MSG_ERROR([You need to have python-hachoir-regex installed])
fi


dnl checking operative system
dnl --------------------------------------------

SYSCONFDIR_TMP="$sysconfdir"
EXPANDED_SYSCONFDIR=`eval echo $SYSCONFDIR_TMP`
AC_SUBST(EXPANDED_SYSCONFDIR)

operating_system=unknown

AC_MSG_CHECKING(Checking Redhat)
if test -f /etc/redhat-release || test -f $EXPANDED_SYSCONFDIR/redhat-release ; then
   AC_MSG_RESULT(found)
   operative_system=redhat
else
   AC_MSG_RESULT(not found)
fi

AC_MSG_CHECKING(Checking Suse)
if test -f /etc/SuSE-release || test -f $EXPANDED_SYSCONFDIR/SuSE-release ; then
   AC_MSG_RESULT(found)
   operative_system=suse
else
   AC_MSG_RESULT(not found)
fi

AC_MSG_CHECKING(Checking Debian/Ubuntu)
if test -f /etc/debian_version || test -f $EXPANDED_SYSCONFDIR/debian_version ; then
   AC_MSG_RESULT(found)
   operative_system=debian
else
   AC_MSG_RESULT(not found)
fi

AM_CONDITIONAL(NANNY_INIT_SCRIPTS_RED_HAT, test x$with_init_scripts = xredhat)
AM_CONDITIONAL(NANNY_INIT_SCRIPTS_SUSE, test x$with_init_scripts = xsuse)
AM_CONDITIONAL(NANNY_INIT_SCRIPTS_DEBIAN, test x$with_init_scripts = xdebian)


dnl *******************************
dnl Internationalization
dnl *******************************
GETTEXT_PACKAGE=nanny
AC_DEFINE(GETTEXT_PACKAGE, "$GETTEXT_PACKAGE", "nanny")
AC_SUBST(GETTEXT_PACKAGE)
GNOME_DOC_INIT

dnl Add the languages which your application supports here.
ALL_LINGUAS="es vi"

AM_GLIB_GNU_GETTEXT
AC_PROG_INTLTOOL

AC_OUTPUT([
Makefile
po/Makefile.in
client/Makefile
client/common/Makefile
client/common/src/Makefile
client/common/icons/Makefile
client/common/icons/16x16/Makefile
client/common/icons/22x22/Makefile
client/common/icons/24x24/Makefile
client/common/icons/32x32/Makefile
client/common/icons/48x48/Makefile
client/common/icons/256x256/Makefile
client/common/icons/scalable/Makefile
client/gnome/Makefile
client/gnome/systray/Makefile
client/gnome/systray/src/Makefile
client/gnome/systray/src/__init__.py
client/gnome/systray/data/Makefile
client/gnome/admin/Makefile
client/gnome/admin/data/Makefile
client/gnome/admin/data/ui/Makefile
client/gnome/admin/data/icons/Makefile
client/gnome/admin/src/Makefile
client/gnome/admin/src/__init__.py
daemon/Makefile
daemon/data/Makefile
daemon/data/applists/Makefile
daemon/data/dbus/Makefile
daemon/data/init.d/Makefile
daemon/data/init.d/debian/Makefile
daemon/data/init.d/redhat/Makefile
daemon/data/init.d/suse/Makefile
daemon/src/Makefile
daemon/src/proxy/Makefile
help/Makefile
man/Makefile
])

echo "
		NANNY
		=====

	prefix:				 ${prefix}

"
