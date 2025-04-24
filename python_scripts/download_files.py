#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse
import re
import shutil
from pathlib import Path

SPLIT_LINE = "-----------------------------------------------------------------------------------------------------------"
USERNAME = "luoshanguo"
PASSWORD = "luoshanguo"
LOCAL_DIR = "/home/rdma"
FILE_TYPE = "rpd"

def usage():
    """Display the usage information and exit.
    """
    print(SPLIT_LINE)
    print(f"Usage: {sys.argv[0]} -f file_url [-u username] [-p password] [-l local_dir] [-t file_type]")
    print(SPLIT_LINE)
    sys.exit(1)

def install_smbclient():
    """Check if smbclient is installed, and install it if not present.
    """
    if shutil.which("smbclient") is None:
        print("smbclient not found, installing...")
        try:
            if os.path.exists("/etc/centos-release") or os.path.exists("/etc/redhat-release"):
                # CentOS/RHEL
                subprocess.run(["sudo", "yum", "install", "-y", "samba-client"], check=True)
            elif os.path.exists("/etc/lsb-release") or os.path.exists("/etc/os-release"):
                # Ubuntu/Debian
                subprocess.run(["sudo", "apt-get", "update"], check=True)
                subprocess.run(["sudo", "apt-get", "install", "-y", "smbclient"], check=True)
            else:
                print("Unsupported operating system.")
                sys.exit(1)
            print("smbclient installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install smbclient: {e}")
            sys.exit(1)
    else:
        print("smbclient is already installed.")

def process_url(url):
    """Process the provided URL into segments.
    :param url: The URL to process (string).
    :return: A string with processed URL segments separated by spaces.
    """
    # Convert backslashes to spaces and remove leading double backslashes
    url = re.sub(r'^\\\\', '', url).replace('\\', ' ')
    # Remove prefix before "://" and replace "/" with spaces
    url = re.sub(r'^[^:]+://', '', url).replace('/', ' ')
    return url

def main():
    """Main function to handle SMB file download and MD5 calculation.
    """
    global USERNAME, PASSWORD, LOCAL_DIR, FILE_TYPE

    # Parse command-line arguments
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-f', '--file-url', required=True, help="The URL of the file or directory to download")
    parser.add_argument('-u', '--username', default=USERNAME, help="Username for SMB authentication")
    parser.add_argument('-p', '--password', default=PASSWORD, help="Password for SMB authentication")
    parser.add_argument('-l', '--local-dir', default=LOCAL_DIR, help="Local directory to save downloaded files")
    parser.add_argument('-t', '--file-type', default=FILE_TYPE, help="File type to filter (e.g., 'rpd')")
    args = parser.parse_args()

    FILE_URL = args.file_url
    USERNAME = args.username
    PASSWORD = args.password
    LOCAL_DIR = args.local_dir
    FILE_TYPE = args.file_type

    # Install smbclient if not present
    install_smbclient()

    print(f"file URL: {FILE_URL}")
    url_seg = process_url(FILE_URL)
    print(f"Processed URL: {url_seg}")

    # Extract server, share, and directory path
    url_seg_list = url_seg.split()
    if len(url_seg_list) < 2:
        print("Invalid URL format. Expected at least server and share.")
        sys.exit(1)
    SERVER = url_seg_list[0]
    SHARE = url_seg_list[1]
    DIR_PATH = '/'.join(url_seg_list[2:]) if len(url_seg_list) > 2 else ""

    print(SPLIT_LINE)
    print(f"SERVER   :  {SERVER}")
    print(f"SHARE    :  {SHARE}")
    print(f"DIR_PATH :  {DIR_PATH}")
    print(f"FILE_TYPE:  {FILE_TYPE}")
    print(SPLIT_LINE)

    # Determine download directory and filename
    if DIR_PATH.endswith(f".{FILE_TYPE}"):
        dowlaod_dir_path = os.path.dirname(DIR_PATH) or ""
        dowlaod_filename = os.path.basename(DIR_PATH)
    else:
        dowlaod_dir_path = DIR_PATH
        dowlaod_filename = ""

    # Create local directory if it doesn't exist
    if not os.path.isdir(LOCAL_DIR):
        print(SPLIT_LINE)
        print(f"Local directory {LOCAL_DIR} does not exist. Creating...")
        os.makedirs(LOCAL_DIR, exist_ok=True)
        print(f"Directory {LOCAL_DIR} created.")
        print(SPLIT_LINE)

    # List directory contents using smbclient
    cmd = f"smbclient '//{SERVER}/{SHARE}' -U '{USERNAME}%{PASSWORD}' -c 'cd {dowlaod_dir_path}; ls'"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        DIR_LISTING = result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Failed to list directory: {e}")
        sys.exit(1)
    print("Directory listing:")
    print(DIR_LISTING)
    print(SPLIT_LINE)

    # Filter files to download
    if dowlaod_filename:
        download_files = [dowlaod_filename] if dowlaod_filename in DIR_LISTING else []
    else:
        download_files = re.findall(rf"\S+\.{FILE_TYPE}", DIR_LISTING)

    print("Download Files:")
    print("\n".join(download_files) if download_files else "")
    print(SPLIT_LINE)

    # Check if files were found
    if not download_files:
        print(SPLIT_LINE)
        if not dowlaod_filename:
            print(f"No .{FILE_TYPE} files found in the specified directory.")
        else:
            print(f"File {dowlaod_filename} not found in the specified directory.")
        print(SPLIT_LINE)
        sys.exit(1)

    # Download files and calculate MD5
    for dfile in download_files:
        print(SPLIT_LINE)
        print(f"Downloading file {dfile} ...")
        cmd = f"smbclient '//{SERVER}/{SHARE}' -U '{USERNAME}%{PASSWORD}' -c 'cd {dowlaod_dir_path}; lcd {LOCAL_DIR}; get {dfile}'"
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to download {dfile}: {e}")
            sys.exit(1)

        # Calculate MD5 of the downloaded file
        local_file = os.path.join(LOCAL_DIR, dfile)
        try:
            md5_result = subprocess.run(["md5sum", local_file], capture_output=True, text=True, check=True)
            LOCAL_MD5 = md5_result.stdout.split()[0]
        except subprocess.CalledProcessError as e:
            print(f"Failed to calculate MD5 for {dfile}: {e}")
            sys.exit(1)

        print(SPLIT_LINE)
        print(f"Calculate MD5 for {dfile}:")
        print(f"MD5: {LOCAL_MD5}")
        print(SPLIT_LINE)

    print(SPLIT_LINE)

if __name__ == "__main__":
    main()