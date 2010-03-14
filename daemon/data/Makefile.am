SUBDIRS=applists dbus init.d

policy_in_files = org.gnome.nanny.policy.in
policydir = $(POLKIT_POLICY_DIR)
policy_DATA = $(policy_in_files:.policy.in=.policy)
@INTLTOOL_POLICY_RULE@

EXTRA_DIST= org.gnome.nanny.policy.in
