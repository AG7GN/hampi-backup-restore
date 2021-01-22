# nexus-backup-restore

Version 20210122

Scripts to backup/restore home folder and to backup and compress the entire microSD card.

## nexus-backup-restore.sh

This script will back up the contents of your home folder on your Nexus Pi to an external (USB attached) disk or flash drive.
 
This script is handy when you're moving to a new image. In that case, run it on your Pi to create a backup of your home folder, then insert the SD card with the new image, run this scrip again and insert the USB stick with your backup, click Restore and follow the prompts.

## sdbackup.py

This script will backup and compress the entire microSD card to an external (USB attached) disk or flash drive. It can be run from the command line and do scheduled backups via a cron job, or be run interactively as a GUI.  The script creates a file in the destination disk that the user selects. The backup file name is of this format:

	$HOSTNAME_xGB_YYYYMMDDTHHmmSS.gz
	
where `$HOSTNAME` is the hostname of the Raspberry Pi., `x` is the size of the microSD card that's being backed up (the script determines this), `YYYY` is the year,  `MM` the month, `DD` day of the month, `T` separates the date from the time, `HH` the hour, `mm` the minute, and `ss` the second when the backup was started. `gz` is the file extension, indicating a 'gzipped' file.

The USB drive containing the backup file can then be moved to any Mac or Linux or Windows PC and the backup `gz` file can be burned to a microSD card using [Balena Etcher](https://www.balena.io/etcher/). The `gz` file does not have to be uncompressed first. Balena Etcher automatically decompresses it. 

Note that when you burn the backup `gz` file to a microSD card, that card must be the same size as or larger than the microSD card from which the backup was made. That's why I embedded the original microSD card size into the file name.

On a Raspberry Pi 4B with a 16GB microSD card (about half full) with 4GB RAM and a USB3 HDD attached to a USB3 port, the backup takes just over an hour and results in a `gz` file of about 6GB.

### Prerequisites

- The USB attached external disk/flash drive must be formatted as `exfat`, which supports files larger than 4GB. [`exfat` formatted](https://recoverit.wondershare.com/usb-tips/format-usb-drive-to-exfat.html) disks can be read by Linux, Mac and Windows PCs. `ext4` formatted disks are also supported, but those disks cannot be read by Macs or Windows PCs. The script will print an error message if the external drive uses a format that does not support files larger than 4GB.

- There must be adequate space on the external disk/flash drive. The script will make a guess at how much space will be needed on the external drive for the compressed image and will print an error if it determines that there is not enough space available.

- The script must be run with `root` privileges (`sudo`).

- The Raspbian OS must have the `exfat-utils` package installed. This is installed by default on the NexusDR-X image.

- NOTE: The Raspbian OS by default automatically detects disks plugged in to USB and in most cases, a shortcut will automatically appear on the desktop for that disk. You'll also likely see a "__Removable medium inserted__" window popup when the disk is attached to a USB port. Just click __Cancel__ to close that window. USB attached drives appear as:

	/media/`$USER`/__*name-of-drive*__ 

	where `$USER` is usually `pi`.

### Run from the command line

- Run the script with the `-h` to see the available options. For example:

		pi@buildpi:~ $ sudo sdbackup.py -h
		usage: ddbackup.py [-h] [-v] [-d STRING]

		Backup & compress Raspberry Pi Image

		optional arguments:
		  -h, --help            show this help message and exit
		  -v, --version         show program's version number and exit
		  -d STRING, --destination STRING
					  Destination path/location for the backup

- If `sdbackup.py` is run with the `-d` or `--destination` option followed by the destination location, the script will run entirely on the command line. No GUI will open.

	For example, to backup my microSD card to my USB attached disk at `/media/pi/500GB`, I would run:
	
		sudo sdbackup.py -d /media/pi/500GB


### Run as a `cron` job

You can set up your Pi to do automatic unattended backups via [cron](https://linuxize.com/post/scheduling-cron-jobs-with-crontab/) of your microSD card. In this example, I'll backup up my microSD card to a USB disk drive connected to my Pi. My external disk appears as `500GB` on my desktop, so the path to that disk is: `/media/pi/500GB`.

I'll set up the script to run every Sunday at 2:13 AM. The script will also delete backups older than 14 days and verify that the external disk is attached before attempting to run the backup.

- Run `crontab -e` to open the cron editor. You might be prompted to select an editor. `nano` is easiest to use.

- Add the following line to the end of the file (IMPORTANT: change `/media/pi/500GB` to match your attached disk and adjust the time/frequency as desired):

		13 2 * * 0 [ -d /media/pi/500GB ] && (sudo find /media/pi/500GB/$HOSTNAME_*GB_*.gz -maxdepth 1 -type f -mtime +14 -delete; sudo sdbackup.py -d /media/pi/500GB >/dev/null 2>&1)

	The line above breaks down as follows:
	
	- `13 2 * * 0`: Run this script at 13 minutes after 2AM regardless of the day of the month (the 1st `*`) regardless of the month (the 2nd `*`) every Sunday (the `0`).
	- `[ -d /media/pi/500GB ] &&`: Verify that `/media/pi/500GB` exists and is a directory, and if it is (`&&`), execute the remainder of the line. If `/media/pi/500GB` is not present or is not a directory, the job ends here.
	- `(sudo find /media/pi/500GB/$HOSTNAME_*GB_*.gz -maxdepth 1 -type f -mtime +14 -delete`: Look for files (`-type f`) matching this criteria: `/media/pi/500GB/$HOSTNAME_*GB_*.gz`. If any matching files are older than 14 days (`-mtime +14`) , delete (`-delete`) them. Don't look for any matching files in any subdirectories (`-maxdepth 1`), then once that's done (`;`)...
	- `sudo sdbackup.py -d /media/pi/500GB >/dev/null 2>&1)`: ...run the backup script and send any printed output from `sdbackup.py` to the bit bucket (`>/dev/null 2>&1`).
	
- Save the file and exit the editor. The script will run automatically at 2:13AM every Sunday.

### Run the GUI

If you don't provide any arguments, `sdbackup.py` will attempt to start the GUI.

- A dialog will appear that will prompt you to select the destination for the backup. Click __OK__ once you've selected the destination.
- If the destination is valid and has enough available space, another dialog window appears. Click __Start__ to begin the backup. You can monitor the backup progress via the progress bar and the % complete indicator.
- When the backup has completed, click __Quit__ to close the script. Clicking __Quit__ while the backup is running will abort the backup and delete the backup file.


