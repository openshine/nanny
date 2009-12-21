#! /bin/sh
#
# skeleton	example file to build /etc/init.d/ scripts.
#		This file should be used to construct scripts for /etc/init.d.
#
#		Written by Miquel van Smoorenburg <miquels@cistron.nl>.
#		Modified for Debian 
#		by Ian Murdock <imurdock@gnu.ai.mit.edu>.
#
# Version:	@(#)skeleton  1.9  26-Feb-2001  miquels@cistron.nl
#

PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

NANNY_TAP="/usr/share/nanny/daemon/nanny.tap"

if [ -e /usr/local/share/nanny/daemon/nanny.tap ] ;
then
    NANNY_TAP="/usr/local/share/nanny/daemon/nanny.tap"
fi


NAME="nanny"
DESC="nanny (Parental Control Daemon)"
PID_FILE="/var/run/$NAME.pid"
LOG_FILE="/var/log/nanny.log"

TWISTD=$(which twistd)
DAEMON="$TWISTD -- --uid root --gid root --pidfile $PID_FILE -r glib2 --logfile $LOG_FILE -y $NANNY_TAP "

test -e $TWISTD
test -e $NANNY_TAP

# Include nanny defaults if available
if [ -f /etc/default/nanny ] ; then
	. /etc/default/nanny
fi

set -e


case "$1" in
  start)
        if [ ! -e $PID_FILE ] ;
        then
            echo -n "Starting $DESC: "
            start-stop-daemon --start --quiet --pidfile $PID_FILE --exec $DAEMON
            echo "$NAME."
        fi

	;;
  stop)
	if [ -e $PID_FILE ] ;
        then
            echo -n "Stopping $DESC: "
            start-stop-daemon --stop --quiet --pidfile $PID_FILE
            echo "$NAME."
        fi
	;;
  
  restart|force-reload)
	$0 stop
	sleep 1
	$0 start
	;;
  *)
	N=/etc/init.d/$NAME
	# echo "Usage: $N {start|stop|restart|reload|force-reload}" >&2
	echo "Usage: $N {start|stop|restart|force-reload}" >&2
	exit 1
	;;
esac

exit 0
