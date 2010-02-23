include $(top_srcdir)/gnome-doc-utils.make
dist-hook: doc-dist-hook

DOC_MODULE = nanny
DOC_ENTITIES = legal.xml nanny.xml
DOC_INCLUDES = 
DOC_FIGURES = figures/nanny-add-forbidden-site.png                   \
              figures/nanny-select-file-to-import.png                \
              figures/nanny-session.png                              \
              figures/nanny-web-content-filter-blacklists.png
DOC_LINGUAS = cs de es

helpdir = $(datadir)/gnome/help/nanny/C/
help_DATA = C/nanny.xml                                              \
            C/figures/nanny-add-forbidden-site.png                   \
            C/figures/nanny-select-file-to-import.png                \
            C/figures/nanny-session.png                              \
            C/figures/nanny-web-content-filter-blacklists.png

EXTRA_DIST=$(help_DATA)

