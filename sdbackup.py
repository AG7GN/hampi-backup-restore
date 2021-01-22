#!/usr/bin/env python3
import sys
import signal
import os
import stat
import subprocess
import json
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import shutil
import datetime
import gzip
import time


__author__ = "Steve Magnuson AG7GN"
__copyright__ = "Copyright 2020, Steve Magnuson"
__credits__ = ["Steve Magnuson"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Steve Magnuson"
__email__ = "ag7gn@arrl.net"
__status__ = "Production"


run_backup = True
block_device = "mmcblk0"
disk = f"/dev/{block_device}"


def sigint_handler(sig, frame):
    print(f"Signal handler caught {sig} {frame}")
    cleanup()


def find_mount_point(path: str) -> str:
    path = os.path.abspath(path)
    while not os.path.ismount(path):
        path = os.path.dirname(path)
    return path


def space_available(path: str) -> bool:
    _, _, destination_free = shutil.disk_usage(path)
    _, root_used, _ = shutil.disk_usage('/')
    _, boot_used, _ = shutil.disk_usage('/boot')
    sd_used = root_used + boot_used
    if destination_free > sd_used:
        return True
    else:
        return False


def valid_fstype(mount: str):

    cmd = f"lsblk -J -b -o +FSTYPE"
    try:
        _result = subprocess.check_output(cmd, shell=True).decode('utf-8')
    except subprocess.CalledProcessError as e:
        return False, f"ERROR: {e}. Executing {cmd}"
    json_object = json.loads(_result)
    # print(json.dumps(json_object, indent=4))
    for i in range(0, len(json_object['blockdevices'])):
        if json_object['blockdevices'][i]['name'] == block_device:
            continue  # Skip the microSD card as a possible destination
        try:
            _mount = json_object['blockdevices'][i]['children']
        except KeyError:  # Doesn't contain 'children'
            _mount = [json_object['blockdevices'][i], ]
        if _mount[0]['mountpoint'] == mount:
            if _mount[0]['fstype'] != 'vfat':
                return True, None
            else:
                return False, f"ERROR: '{mount}' is type vfat and does not " \
                              f"support files larger than 4GB. Use an exfat " \
                              f"or ext4 formatted disk."
    return False, f"ERROR: Destination is on the microSD card. " \
                  f"Can't back up to this device."


def progress_percentage(perc, width=None):
    # This will only work for python 3.3+ due to use of
    # os.get_terminal_size the print function etc.
    # Source: https://stackoverflow.com/questions/29967487/get-progress-back-from-shutil-file-copy-thread

    _full_block = '█'
    # this is a gradient of incompleteness
    _incomplete_block_grad = ['░', '▒', '▓']
    assert(isinstance(perc, float))
    assert(0. <= perc <= 100.)
    # if width unset use full terminal
    if width is None:
        width = os.get_terminal_size().columns
    # progress bar is block_widget separator perc_widget : ####### 30%
    max_perc_widget = '[100.00%]'  # 100% is max
    separator = ' '
    blocks_widget_width = width - len(separator) - len(max_perc_widget)
    assert(blocks_widget_width >= 10)  # not very meaningful if not
    perc_per_block = 100.0/blocks_widget_width
    # epsilon is the sensitivity of rendering a gradient block
    epsilon = 1e-6
    # number of blocks that should be represented as complete
    _full_blocks = int((perc + epsilon)/perc_per_block)
    # the rest are "incomplete"
    empty_blocks = blocks_widget_width - _full_blocks

    # build blocks widget
    blocks_widget = ([_full_block] * _full_blocks)
    blocks_widget.extend([_incomplete_block_grad[0]] * empty_blocks)
    # marginal case - remainder due to how granular our blocks are
    remainder = perc - _full_blocks*perc_per_block
    # epsilon needed for rounding errors (check would be != 0.)
    # based on reminder modify first empty block shading
    # depending on remainder
    if remainder > epsilon:
        grad_index = int((len(_incomplete_block_grad) * remainder)/perc_per_block)
        blocks_widget[_full_blocks] = _incomplete_block_grad[grad_index]

    # build perc widget
    str_perc = '%.2f' % perc
    # -1 because the percentage sign is not included
    perc_widget = '[%s%%]' % str_perc.ljust(len(max_perc_widget) - 3)

    # form progressbar
    progress_bar = '%s%s%s' % (''.join(blocks_widget), separator, perc_widget)
    # return progressbar as string
    return ''.join(progress_bar)


def copy_progress(copied, total):
    print('\r' + progress_percentage(100*copied/total, width=30), end='')


def backup(path: str, callback=None, block_size=1024*1024):
    """
    Performs a gzipped copy of the microSD card (/dev/mmcblk0) to an
    external drive.

    :param path: Path to the destination
    :param callback: Optional callback function for progress reporting
    :param block_size amount of data in bytes to read/write at a time
    :return: Tuple of 2 strings: destination-path/file and elapsed
            backup time (HH:MM:SS)
    """
    sd_card_size = shutil.disk_usage('/')[0] + shutil.disk_usage('/boot')[0]
    # sd_card_size = 100*1024*1024
    now = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
    zip_file = f"{os.uname()[1]}_{round(sd_card_size / 1000000000)}GB_{now}.gz"
    copied = 0
    start = int(time.time())
    try:
        with open(disk, 'rb') as file_in, \
                gzip.open(f"{path}/{zip_file}", 'wb') as file_out:
            while run_backup:
                block = file_in.read(block_size)
                # if not block:
                if not block or copied >= sd_card_size:
                    break
                file_out.write(block)
                copied += block_size
                if callback:
                    # Make sure copied doesn't exceed sd_card_size,
                    # which will likely happen on the last block.
                    callback(min(max(copied, 0), sd_card_size), total=sd_card_size)
    except IOError:
        # print("I/O ERROR({0}): {1}".format(e.errno, e.strerror),
        #       file=sys.stderr)
        return f"{path}/{zip_file}", None
    # except: #handle other exceptions such as attribute errors
    #     print("Unexpected error:", sys.exc_info()[0])
    if os.path.isfile(f"{path}/{zip_file}") and not run_backup:
        os.remove(f"{path}/{zip_file}")
        return f"{path}/{zip_file}", None
    end = int(time.time())
    elapsed = end - start
    return f"{path}/{zip_file}", f"{datetime.timedelta(seconds=elapsed)}"


def increment(copied, total):
    value = 100*copied/total
    progress['value'] = value
    label.config(text=f"{'{:.2f}'.format(value)}% complete")
    root.update()


def copy_progress_gui():
    start_button.config(state="disabled")
    _backup_file, _elapsed_time = backup(root.directory, callback=increment)
    if _elapsed_time is None:
        print(f"ERROR: Backup failed or aborted", file=sys.stderr)
        sys.exit(1)
    else:
        label.configure(text=f"Backup to\n {_backup_file} \ncompleted in {_elapsed_time}")
        root.update()


def validate_destination(dest: str):
    if os.path.isdir(dest):
        _ok, _message = valid_fstype(find_mount_point(dest))
        if _ok:
            if space_available(dest):
                return True, None
            else:
                return False, f"Not enough space available on '{dest}'"
        else:
            return False, _message
    else:
        return False, f"'{dest}' is not a directory"


def cleanup():
    global run_backup
    run_backup = False
    root.quit()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(prog='ddbackup.py',
                                     description=f"Backup & compress Raspberry Pi Image")
    parser.add_argument('-v', '--version', action='version',
                        version=f"Version: {__version__}")
    parser.add_argument("-d", "--destination",
                        type=str, metavar="STRING",
                        help="Destination path/location for the backup")
    arg_info = parser.parse_args()
    try:
        stat.S_ISBLK(os.stat(disk).st_mode)
    except FileNotFoundError:
        print(f"ERROR: This application only works on Linux systems with '{disk}'",
              file=sys.stderr)
        sys.exit(1)
    if os.geteuid() != 0:
        print(f"ERROR: This application must be run with root privileges",
              file=sys.stderr)
        sys.exit(1)
    if arg_info.destination:
        dest_ok, message = validate_destination(arg_info.destination)
        if dest_ok:
            dest_file, elapsed_time = backup(arg_info.destination,
                                             callback=copy_progress)
            if elapsed_time is None:
                print(f"ERROR: Backup failed or aborted", file=sys.stderr)
                sys.exit(1)
            else:
                print(f"\nBackup to {dest_file} completed in {elapsed_time}")
                sys.exit(0)
        else:
            print(message, file=sys.stderr)
            sys.exit(1)
    # If we made it this far, no arguments were supplied. Attempt
    # to open GUI.
    if os.environ.get('DISPLAY', '') == '':
        print(f"ERROR: No $DISPLAY environment. "
              f"Must supply destination to run without X", file=sys.stderr)
        sys.exit(1)
        # os.environ.__setitem__('DISPLAY', ':0.0')

    root = tk.Tk()
    # root.resizable(width=True, height=True)
    signal.signal(signal.SIGINT, sigint_handler)
    # Stop program if Esc key pressed
    root.bind('<Escape>', lambda _: cleanup())
    # Stop program if window is closed at OS level ('X' in upper right
    # corner or red dot in upper left on Mac)
    root.protocol("WM_DELETE_WINDOW", lambda: cleanup())
    # Place all windows close to the center of the screen
    root.withdraw()
    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_reqwidth()) / 2
    y = (root.winfo_screenheight() - root.winfo_reqheight()) / 2
    root.geometry("+%d+%d" % (x, y))
    while True:
        if os.path.isdir('/media'):
            initial_dir = "/media"
        else:
            initial_dir = "/"
        root.directory = filedialog.askdirectory(mustexist=True,
                                                 title=f"SDBackup {__version__} Select destination",
                                                 initialdir=initial_dir)
        if not root.directory:
            root.quit()
            break
        dest_ok, message = validate_destination(root.directory)
        if dest_ok:
            root.title(f"SDBackup {__version__}")
            root.deiconify()
            progress = ttk.Progressbar(root, orient="horizontal",
                                       length=350, mode='determinate')
            progress.pack(pady=10)
            label = ttk.Label(root, text="Click Start to begin backup",
                              relief="flat", borderwidth=1,
                              anchor="center", justify="center",
                              font=(None, 12,))
            label.pack(padx=10, pady=5, fill="both")
            start_button = ttk.Button(root, text="Start",
                                      command=copy_progress_gui)
            start_button.pack(side=tk.LEFT, padx=20, pady=10)
            ttk.Button(root, text="Quit", command=cleanup).pack(side=tk.RIGHT,
                                                                padx=20,
                                                                pady=10)
            root.mainloop()
            break
        else:
            messagebox.showerror(f"SDBackup {__version__}", message)
    sys.exit(0)
