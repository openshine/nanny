
import sys, os, glob, stat

# ...
# ModuleFinder can't handle runtime changes to __path__, but win32com uses them
try:
    # py2exe 0.6.4 introduced a replacement modulefinder.
    # This means we have to add package paths there, not to the built-in
    # one.  If this new modulefinder gets integrated into Python, then
    # we might be able to revert this some day.
    # if this doesn't work, try import modulefinder
    try:
        import py2exe.mf as modulefinder
    except ImportError:
        import modulefinder
    import win32com
    for p in win32com.__path__[1:]:
        modulefinder.AddPackagePath("win32com", p)
    for extra in ["win32com.shell"]: #,"win32com.mapi"
        __import__(extra)
        m = sys.modules[extra]
        for p in m.__path__[1:]:
            modulefinder.AddPackagePath(extra, p)
except ImportError:
    # no build path setup, no worries.
    pass


nanny_top_dir = os.path.dirname(os.path.dirname(__file__))
nanny_win32_dist_dir = os.path.join(nanny_top_dir, "Nanny")
nanny_python_dir = os.path.join(nanny_top_dir, "lib", "python2.6", "site-packages")

sys.path.append(nanny_python_dir)

if len(sys.argv) == 1:
    sys.argv.append("py2exe")

from distutils.core import setup
import py2exe

ver = "2.30"
py2exe_options = dict (
    packages = "encodings",
    includes = ["sqlite3", "cairo", "pango", "pangocairo", "atk", "gobject"],
    )

#Share
def walktree (top = ".", depthfirst = True):
    names = os.listdir(top)
    if not depthfirst:
        yield top, names
    for name in names:
        try:
            st = os.lstat(os.path.join(top, name))
        except os.error:
            continue
        if stat.S_ISDIR(st.st_mode):
            for (newtop, children) in walktree (os.path.join(top, name), depthfirst):
                yield newtop, children
    if depthfirst:
        yield top, names

share_files = []
etc_files = []

for (basepath, children) in walktree(os.path.join(nanny_top_dir, "share"),False):
    for child in children:
        if os.path.isfile(os.path.join(basepath, child)):
            share_files.append(os.path.join(basepath, child))

for (basepath, children) in walktree(os.path.join(nanny_top_dir, "etc"),False):
    for child in children:
        if os.path.isfile(os.path.join(basepath, child)):
            etc_files.append(os.path.join(basepath, child))

data_files = {}
for file in share_files + etc_files:
    path_dir = os.path.dirname(file).replace(nanny_top_dir, os.path.join("Nanny\\"))
    if path_dir not in data_files.keys():
        data_files[path_dir] = []
    data_files[path_dir].append(file)

dist_files = []
for key in data_files : 
    dist_files.append([key, data_files[key]])

dist_files

#Setup of py2exe

daemon_service_dbg = dict(
    script = os.path.join(nanny_top_dir, "sbin", "NannyService.py"),
    dest_base = os.path.join("Nanny", "bin", "nanny-daemon-dbg"),
)

daemon_service = dict(
    script = os.path.join(nanny_top_dir, "sbin", "NannyService.py"),
    dest_base = os.path.join("Nanny", "bin", "NannyService"),
    modules=["NannyService"],
    cmdline_style='pywin32',
)

admin_console_dbg = dict(
    script = os.path.join(nanny_top_dir, "sbin", "nanny-admin-console"),
    dest_base = os.path.join("Nanny", "bin", "nanny-admin-console-dbg"),
)

admin_console = dict(
    script = os.path.join(nanny_top_dir, "sbin", "nanny-admin-console"),
    dest_base = os.path.join("Nanny", "bin", "nanny-admin-console"),
    icon_resources = [(1, "nanny-32x32.ico")],
)

dblocker_dbg = dict(
    script = os.path.join(nanny_top_dir, "sbin", "nanny-desktop-blocker"),
    dest_base = os.path.join("Nanny", "bin", "nanny-desktop-blocker-dbg"),
)

dblocker = dict(
    script = os.path.join(nanny_top_dir, "sbin", "nanny-desktop-blocker"),
    dest_base = os.path.join("Nanny", "bin", "nanny-desktop-blocker"),
)

ffblocker_dbg = dict(
    script = os.path.join(nanny_top_dir, "sbin", "nanny-firefox-blocker"),
    dest_base = os.path.join("Nanny", "bin", "nanny-firefox-blocker-dbg"),
)

ffblocker = dict(
    script = os.path.join(nanny_top_dir, "sbin", "nanny-firefox-blocker"),
    dest_base = os.path.join("Nanny", "bin", "nanny-firefox-blocker"),
    icon_resources = [(1, "nanny-32x32.ico")],
)

tray_dbg = dict(
    script = os.path.join(nanny_top_dir, "bin", "nanny-systray"),
    dest_base = os.path.join("Nanny", "bin", "nanny-systray-dbg"),
)

tray = dict(
    script = os.path.join(nanny_top_dir, "bin", "nanny-systray"),
    dest_base = os.path.join("Nanny", "bin", "nanny-systray"),
)

setup(name="Nanny",
      version=ver,
      description="Nanny parental control",
      #com_server=[outlook_addin],
      console=[daemon_service_dbg, admin_console_dbg, dblocker_dbg, ffblocker_dbg, tray_dbg],
      windows=[admin_console, dblocker, ffblocker, tray],
      service=[daemon_service],
      data_files = dist_files,
      options = {"py2exe" : py2exe_options},
      zipfile = os.path.join("Nanny", "lib", "nannylib.zip"),
)
