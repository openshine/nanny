
import sys, os, glob, stat

nanny_top_dir = os.path.dirname(os.path.dirname(__file__))
nanny_win32_dist_dir = os.path.join(nanny_top_dir, "NannyW32")
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
    path_dir = os.path.dirname(file).replace(nanny_top_dir, os.path.join("NannyW32\\"))
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
    dest_base = os.path.join("NannyW32", "bin", "nanny-daemon-dbg"),
)

daemon_service = dict(
    script = os.path.join(nanny_top_dir, "sbin", "NannyService.py"),
    dest_base = os.path.join("NannyW32", "bin", "NannyService"),
    modules=["NannyService"],
    cmdline_style='pywin32',
)

admin_console_dbg = dict(
    script = os.path.join(nanny_top_dir, "sbin", "nanny-admin-console"),
    dest_base = os.path.join("NannyW32", "bin", "nanny-admin-console-dbg"),
)

admin_console = dict(
    script = os.path.join(nanny_top_dir, "sbin", "nanny-admin-console"),
    dest_base = os.path.join("NannyW32", "bin", "nanny-admin-console"),
)

dblocker_dbg = dict(
    script = os.path.join(nanny_top_dir, "sbin", "nanny-desktop-blocker"),
    dest_base = os.path.join("NannyW32", "bin", "nanny-desktop-blocker-dbg"),
)

dblocker = dict(
    script = os.path.join(nanny_top_dir, "sbin", "nanny-desktop-blocker"),
    dest_base = os.path.join("NannyW32", "bin", "nanny-desktop-blocker"),
)

blacklistmgr_dbg = dict(
    script = os.path.join(nanny_top_dir, "sbin", "nanny-blacklist-manager"),
    dest_base = os.path.join("NannyW32", "bin", "nanny-blacklist-manager-dbg"),
)

blacklistmgr = dict(
    script = os.path.join(nanny_top_dir, "sbin", "nanny-blacklist-manager"),
    dest_base = os.path.join("NannyW32", "bin", "nanny-blacklist-manager"),
)




setup(name="Nanny",
      version=ver,
      description="Nanny parental control",
      #com_server=[outlook_addin],
      console=[daemon_service_dbg, admin_console_dbg, dblocker_dbg, blacklistmgr_dbg],
      windows=[admin_console, dblocker, blacklistmgr],
      service=[daemon_service],
      data_files = dist_files,
      options = {"py2exe" : py2exe_options},
      zipfile = os.path.join("NannyW32", "lib", "nannylib.zip"),
)
