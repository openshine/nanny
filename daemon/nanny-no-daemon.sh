#!/bin/bash

NANNY_TAP="/usr/share/nanny/daemon/nanny.tap"

if [ -e /usr/local/share/nanny/daemon/nanny.tap ] ;
then
    NANNY_TAP="/usr/local/share/nanny/daemon/nanny.tap"
fi

twistd -n --uid root --gid root -r glib2 -y $NANNY_TAP
