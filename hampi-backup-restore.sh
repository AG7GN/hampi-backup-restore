#!/bin/bash

# Script to backup user's home folderi to a tar.gz file,
# or to restore /home/pi from a previously made tar.gz file.

VERSION="1.0.8"
STAMP=$(date +"%Y%m%dT%H%M")
BACKUP_FILE="${HOSTNAME}${STAMP}.tar.gz"

trap errorReport INT

function errorReport () {
   echo
   if [[ $1 == "" ]]
   then
      exit 0
   else
      if [[ $2 == "" ]]
      then
         echo >&2 "$1"
         exit 1
      else
         echo >&2 "$1"
         exit $2
      fi
   fi
}

yad --center --title="$(basename $0) Version $VERSION" --borders=20 \
	 --text-align=center --width=450 \
    --text="<big><b><u>Backup</u></b></big>\nThe contents of <b>$HOME</b> will be archived to a tar.gz file and stored on a \
USB stick or storage device.\n\n \
<big><b><u>Restore</u></b></big>\nA previously made tar.gz archive stored on a USB stick or storage device \
will be extracted to <b>$HOME</b>.  Files in the archive will overwrite \
files of the same name that already exist in <b>$HOME</b>.\n\n \
<big><b>IMPORTANT: Close all other applications before continuing!</b></big>\n\n \
Insert your USB stick or storage device, then click <b>Backup</b> or <b>Restore</b> below.  \
A window will open that will allow you to select the destination device/folder for a Backup, \
or a file for a Restore.  USB sticks and storage devices usually appear in /media/pi." \
    --buttons-layout=center --button=Cancel:0 --button=Backup:1 --button=Restore:2
case $? in
	1)
		BACKUP_FOLDER="$(yad --center --file --directory --title="Select destination folder for backup")"
		[[ $? == 1 || $? == 252 ]] && errorReport  # User has cancelled.

		tar -C $HOME \
          --exclude=.cache \
          --exclude=.debug \
          --exclude=.dbus \
          --exclude=.recently-used \
          --exclude=.thumbnails \
			 --exclude=.xsession-errors \
			 --exclude=.Trash \
          --exclude=Downloads \
          --exclude=configure-autohotspot.sh \
          --exclude=watchdog-tnc.sh \
          --exclude=initialize-pi.sh \
          --exclude=tnc.sh \
          --exclude=dw-*.sh \
          --exclude=trim-f*.sh \
          -cpvzf $BACKUP_FOLDER/$BACKUP_FILE .

      [[ $? != 0 ]] && errorReport "Could not complete backup of $HOME"

      yad --center --title="$(basename $0) Version $VERSION" --info --borders=20 --text-align=center \
          --text="<big><b>Backup complete.</b></big>\n\nArchive is in <b>$BACKUP_FOLDER/$BACKUP_FILE</b>.\n\n \
Eject the USB stick by clicking the eject button on the right side of the desktop menu bar." \
          --buttons-layout=center --button=Close:0
      exit 0
		;;
   2)
      RESTORE_FILE="$(yad --center --file --file-filter="tar.gz files|*.tar.gz" --title="Select archive file to restore from")"
		[[ $? == 1 || $? == 252 ]] && errorReport  # User has cancelled.
		yad --center --title="$(basename $0) Version $VERSION" --question --borders=20 \
			 --text="Contents of <b>$RESTORE_FILE</b> will be restored to <b>$HOME</b>.\n\n \
Existing files with the same name will be overwritten \
by the restored files.\n\n<b>Do you wish to continue?</b>" \
          --text-align=center --buttons-layout=center --button=Cancel:0 --button=Continue:1
		[[ $? != 1 ]] && errorReport  # User has cancelled.
      tar -C $HOME -xpvzf "$RESTORE_FILE"
	   [[ $? != 0 ]] && errorReport	
      yad --center --title="$(basename $0) Version $VERSION" --info --borders=20 --text-align=center \
          --text="<big><b>Restore complete.</b></big>.\n\n \
Eject the USB stick by clicking the eject button on the right side of the desktop menu bar." \
          --buttons-layout=center --button=Close:0
      exit 0
		;;
	*)
      errorReport
		;;
esac

            

