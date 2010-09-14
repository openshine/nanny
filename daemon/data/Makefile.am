SUBDIRS=applists dbus init.d

if NANNY_POSIX_SUPPORT
policy_in_files = org.gnome.nanny.policy.in
policydir = $(POLKIT_POLICY_DIR)
policy_DATA = $(policy_in_files:.policy.in=.policy)
@INTLTOOL_POLICY_RULE@

CLEANFILES = org.gnome.nanny.policy
endif


EXTRA_DIST= org.gnome.nanny.policy.in

