themedir = $(datadir)/icons/hicolor
size = 22x22
context = apps

iconsdir = $(themedir)/$(size)/$(context)

icons_DATA = \
	nanny.png

if NANNY_WIN32_SUPPORT

computercx = devices
webcx = categories
mailcx = emblems
imcx = emotes

computerdir = $(themedir)/$(size)/$(computercx)
webdir = $(themedir)/$(size)/$(webcx)
maildir = $(themedir)/$(size)/$(mailcx)
imdir = $(themedir)/$(size)/$(imcx)

computer_DATA = computer.png
web_DATA = applications-internet.png
mail_DATA = emblem-mail.png
im_DATA = face-smile.png

endif

EXTRA_DIST =				\
	$(icons_DATA)			\
	computer.png			\
	applications-internet.png	\
	emblem-mail.png			\
	face-smile.png
