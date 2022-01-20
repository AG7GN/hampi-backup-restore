#!/bin/bash

# Script to backup user's home folder to a tar.gz file,
# or to restore /home/pi from a previously made tar.gz file.

VERSION="1.2.2"
STAMP=$(date +"%Y%m%dT%H%M")
BACKUP_FILE="${HOSTNAME}_home_${STAMP}.tar.gz"
EXTERNAL_DISKS="/tmp/external_disks"

trap errorReport INT

function errorReport () {
   echo
   if [[ $1 == "" ]]
   then
      exit 0
   else
      if [[ $2 == "" ]]
      then
         echo >&2 -e "$1"
         exit 1
      else
         echo >&2 -e "$1"
         exit $2
      fi
   fi
}

function ExternalDrive () {
	mount -l | grep "^/dev/sd" | grep -vE " / |/boot" | cut -d' ' -f3 >$EXTERNAL_DISKS
	if [[ ! -s $EXTERNAL_DISKS ]]
	then
	   yad --center --title="$(basename $0) Version $VERSION" --info --borders=20 \
   	--text-align=center \
      --text="<big><b>No external disks found!</b></big>\n\n \
<b>Insert a USB disk and then run this script again.<b>"
          --buttons-layout=center --button=Close:0
      exit 1
	fi
}

function TargetNotOnExternalDrive () {
	   yad --center --title="$(basename $0) Version $VERSION" --info --borders=20 \
   	--text-align=center \
      --text="<big><b>$BACKUP_FOLDER</b></big>\n\n \
<b>was not found on any external disk. Try again.</b>" \
          --buttons-layout=center --button=Continue:0
}

SELECTED=0
yad --center --title="$(basename $0) Version $VERSION" --borders=20 \
	--text-align=center --width=650 \
	--text="Attach your USB storage device (it should then be visible as an icon on \
the Desktop), then click <b>Begin Backup</b> or <b>Begin Restore</b> below.  \
A window will open that will allow you to select the destination folder for a Backup, \
or a file for a Restore.\nUSB storage devices usually appear in <b>/media/pi</b>.\n\n \
<big><b><span color='blue'>Backup</span></b></big>\nThe contents of \
<b>$HOME</b> will be archived to a <b>tar.gz</b> file and stored on the attached USB storage device.\n\n \
<big><b><span color='blue'>Restore</span></b></big>\nA previously made <b>tar.gz</b> \
archive file on the attached USB storage device will be restored to <b>$HOME</b>.\n \
<span color='red'><b><i>Files in the archive will <u>overwrite</u> files of the same name that \
already exist in</i> ${HOME}</b></span>\n\n \
<big><b><span color='red'>IMPORTANT:</span> Close all other applications before \
continuing!</b></big>\n" \
  	--buttons-layout=center --button="<b>Cancel Backup/Restore</b>":0 --button="<b>Begin Backup</b>":1 --button="<b>Begin Restore</b>":2
case $? in
	1)
		let SELECTED=0
		while (( $SELECTED == 0 ))
		do
			BACKUP_FOLDER="$(yad --center --file --directory --title="Select destination device/folder for backup")"
			[[ $? == 1 || $? == 252 ]] && errorReport  # User has cancelled.
			ExternalDrive 
			while read DRIVE
			do
				if [[ $BACKUP_FOLDER =~ $DRIVE ]]
				then
					SELECTED=1
					break
				fi
			done <$EXTERNAL_DISKS
			(( $SELECTED == 0 )) && TargetNotOnExternalDrive
		done
			
	  	# Backup crontab
   	crontab -l > $HOME/crontab.$USER
		tar -C $HOME \
        	--exclude=.cache \
        	--exclude=.debug \
       	--exclude=.dbus \
       	--exclude=.gvfs \
			--exclude=.local/share/gvfs-metadata \
			--exclude=.local/share/Trash \
        	--exclude=.recently-used \
        	--exclude=.thumbnails \
		 	--exclude=.xsession-errors \
		 	--exclude=.Trash \
        	--exclude=configure-autohotspot.sh \
        	--exclude=.asoundrc \
        	--exclude=.config/pulse \
        	--exclude=watchdog-tnc.sh \
        	--exclude=initialize-pi.sh \
        	--exclude=tnc.sh \
        	--exclude=dw-*.sh \
        	--exclude=trim-f*.sh \
        	-cpvzf $BACKUP_FOLDER/$BACKUP_FILE . 2>/tmp/$(basename $0).log

     	if [[ $? != 0 ]]
     	then
		   yad --center --title="$(basename $0) Version $VERSION" --info --borders=10 \
   			--text-align=center \
      		--text="<big><b>Could not complete backup of $HOME</b></big>\n\n \
$(cat /tmp/$(basename $0).log)"
          	--buttons-layout=center --button=Close:0
     		errorReport "Could not complete backup of $HOME\n$(cat /tmp/$(basename $0).log)"
     	fi

      yad --center --title="$(basename $0) Version $VERSION" --info --borders=20 --text-align=center \
          --text="<big><b>Backup of $HOME Complete.</b></big>\n\nArchive is in <b>$BACKUP_FOLDER/$BACKUP_FILE</b>.\n\n \
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
by the restored files.\n\n<b>Do you wish to continue?</b>\n" \
          --text-align=center --buttons-layout=center --button="Cancel Restore":0 \
          --button="Continue Restore":1
		[[ $? != 1 ]] && errorReport  # User has cancelled.
      tar -C $HOME -xpvzf "$RESTORE_FILE"
	   [[ $? != 0 ]] && errorReport "Restore failed!"	
	   # Restore crontab
	   [[ -s $HOME/crontab.$USER ]] && crontab $HOME/crontab.$USER
      yad --center --title="$(basename $0) Version $VERSION" --info --borders=20 \
      	--text-align=center \
         --text="<big><b>Restore complete.</b></big>.\n\n \
Eject the USB storage device by clicking the eject button on the right side \
of the desktop menu bar." \
         --buttons-layout=center --button=Close:0
      exit 0
		;;
	*)
      errorReport
		;;
esac

            

