import paramiko
import os
import re

SPLIT_LINE = '-' * 80

class SSH2Connection:
    def __init__(self, ip, username, password, port='22', timeout=600):
        """
        Initialize an SSH connection to a remote host.
        :param ip: IP address of the remote host (string).
        :param username: Username for SSH authentication (string).
        :param password: Password for SSH authentication (string).
        :param port: SSH port number (string, default '22').
        :param timeout: Connection timeout in seconds (int, default 600).
        """
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.ssh_conn = paramiko.SSHClient()
        self.ssh_connection()
        
    def ssh_connection(self):
        """
        Establish an SSH connection to the remote host.
        :return: True if connection is successful, False otherwise.
        """
        print(SPLIT_LINE)
        print(f'SSH connect to {self.ip}...')
        try:
            self.ssh_conn.load_system_host_keys()
            key = paramiko.AutoAddPolicy()
            self.ssh_conn.set_missing_host_key_policy(key)
            self.ssh_conn.connect(self.ip, port=int(self.port), username=self.username, password=self.password, 
                                  timeout=self.timeout)
            return True
        except paramiko.AuthenticationException:
            print("Authentication failed.")
        except paramiko.SSHException as ssh_exception:
            print(f"SSH connection failed: {ssh_exception}")
        return False
    
    def disconnect(self):
        """Close the SSH connection.
        """
        self.ssh_conn.close()

    def execute(self, cmd, timeout=None):
        """
        Execute a command on the remote host via SSH.
        :param cmd: Command to execute (string).
        :param timeout: Command execution timeout in seconds (int, optional).
        :return: Command output (string), including stdout and stderr.
        """
        _, stdout, stderr = self.ssh_conn.exec_command(cmd, timeout=timeout)
        cmd_stdout = stdout.read().decode('utf-8').strip()
        cmd_stderr = stderr.read().decode('utf-8').strip()
        output = cmd_stdout + "\n" + cmd_stderr if cmd_stderr else cmd_stdout
        return output


class Host:
    def __init__(self, ip, username, password):
        """
        Initialize a Host object with SSH connection.
        :param ip: IP address of the host (string).
        :param username: Username for authentication (string).
        :param password: Password for authentication (string).
        """
        self.ip = ip
        self.username = username
        self.password = password
        self.device = SSH2Connection(ip=self.ip, username=self.username, password=self.password)
        self.pf_map = self.get_pf_map()

    def get_pf_map(self):
        """
        Placeholder method to get a platform map (to be implemented).
        :return: A dictionary representing the platform map (currently empty).
        """
        return {}

    def check_and_install_smbclient(self):
        """
        Check if smbclient is installed on the remote host, and install it if not present.
        :return: True if smbclient is available or installed successfully, False otherwise.
        """
        print(SPLIT_LINE)
        print("Checking if smbclient is installed on remote host...")
        check_cmd = "smbclient --version"
        result = self.device.execute(check_cmd)
        
        if "command not found" in result.lower() or "not installed" in result.lower():
            print("smbclient not found, attempting to install...")
            os_check = self.device.execute("cat /etc/os-release || cat /etc/redhat-release")
            if "centos" in os_check.lower() or "red hat" in os_check.lower():
                install_cmd = "sudo yum install -y samba-client"
            elif "ubuntu" in os_check.lower() or "debian" in os_check.lower():
                install_cmd = "sudo apt-get update && sudo apt-get install -y smbclient"
            else:
                print("Unsupported operating system on remote host.")
                return False

            install_result = self.device.execute(install_cmd)
            if "error" in install_result.lower() or "failed" in install_result.lower():
                print(f"Failed to install smbclient: {install_result}")
                return False
            print("smbclient installed successfully.")
            
            verify_result = self.device.execute(check_cmd)
            if "version" in verify_result.lower():
                print("smbclient installation verified.")
                return True
            else:
                print("smbclient installation verification failed.")
                return False
        else:
            print("smbclient is already installed.")
            return True

    def process_smb_url(self, smb_url, file_type="rpd"):
        """
        Process the SMB URL (supports both smb:// and \\server\share formats) to extract server, share, and directory path.
        :param smb_url: SMB URL (e.g., 'smb://server/share/path' or '\\server\share\path') (string).
        :param file_type: File type to filter (e.g., 'rpd') (string, default 'rpd').
        :return: Tuple containing (server, share, download_dir_path, download_filename).
        """
        # Handle both smb:// and UNC (\\) formats
        if smb_url.startswith('\\\\'):
            # Remove leading backslashes and replace remaining backslashes with forward slashes
            url = smb_url[2:].replace('\\', '/')
        else:
            # Remove protocol prefix (e.g., smb://) and replace forward slashes
            url = re.sub(r'^[^:]+://', '', smb_url)
        
        # Split into segments
        url_seg_list = url.split('/')
        if len(url_seg_list) < 2:
            print("Invalid SMB URL format. Expected at least server and share.")
            return None, None, None, None

        server = url_seg_list[0]
        share = url_seg_list[1]
        dir_path = '/'.join(url_seg_list[2:]) if len(url_seg_list) > 2 else ""

        if dir_path.endswith(f".{file_type}"):
            download_dir_path = os.path.dirname(dir_path) or ""
            download_filename = os.path.basename(dir_path)
        else:
            download_dir_path = dir_path
            download_filename = ""

        return server, share, download_dir_path, download_filename

    def list_smb_directory(self, server, share, download_dir_path, smb_username, smb_password):
        """
        List the contents of an SMB directory using smbclient.
        :param server: SMB server address (string).
        :param share: SMB share name (string).
        :param download_dir_path: Directory path within the SMB share (string).
        :param smb_username: Username for SMB authentication (string).
        :param smb_password: Password for SMB authentication (string).
        :return: Directory listing as a string, or None if failed.
        """
        list_cmd = f"smbclient '//{server}/{share}' -U '{smb_username}%{smb_password}' -c 'cd {download_dir_path}; ls'"
        dir_listing = self.device.execute(list_cmd)
        if "NT_STATUS" in dir_listing or "error" in dir_listing.lower():
            print(f"Failed to list SMB directory: {dir_listing}")
            return None
        return dir_listing

    def filter_files_to_download(self, dir_listing, download_filename, file_type="rpd"):
        """
        Filter files to download based on filename or file type.
        :param dir_listing: Directory listing from SMB share (string).
        :param download_filename: Specific filename to download (string, empty if filtering by type).
        :param file_type: File type to filter (e.g., 'rpd') (string, default 'rpd').
        :return: List of filenames to download.
        """
        if not dir_listing:
            return []

        if download_filename:
            return [download_filename] if download_filename in dir_listing else []
        else:
            return re.findall(rf"\S+\.{file_type}", dir_listing)

    def download_smb_files(self, server, share, download_dir_path, download_files, smb_username, smb_password, remote_dir):
        """
        Download SMB files to the remote host and calculate their MD5.
        :param server: SMB server address (string).
        :param share: SMB share name (string).
        :param download_dir_path: Directory path within the SMB share (string).
        :param download_files: List of filenames to download (list of strings).
        :param smb_username: Username for SMB authentication (string).
        :param smb_password: Password for SMB authentication (string).
        :param remote_dir: Directory on the remote host to save files (string).
        :return: List of tuples containing (filename, md5).
        """
        downloaded_files = []
        for dfile in download_files:
            print(SPLIT_LINE)
            print(f"Downloading {dfile} to remote host directory {remote_dir}...")
            download_cmd = f"smbclient '//{server}/{share}' -U '{smb_username}%{smb_password}' -c 'cd {download_dir_path}; lcd {remote_dir}; get {dfile}'"
            download_output = self.device.execute(download_cmd)
            if "NT_STATUS" in download_output or "error" in download_output.lower():
                print(f"Failed to download {dfile}: {download_output}")
                continue

            md5_cmd = f"md5sum {remote_dir}/{dfile}"
            md5_output = self.device.execute(md5_cmd)
            md5_value = md5_output.split()[0] if md5_output and " " in md5_output else "N/A"

            print(f"Remote MD5 for {dfile}: {md5_value}")
            print(SPLIT_LINE)
            downloaded_files.append((dfile, md5_value))

        return downloaded_files

    def smb_download_file(self, smb_url, smb_username, smb_password, remote_dir="/tmp/smb_download", file_type="rpd"):
        """
        Download files from an SMB share to the remote host using smbclient.
        :param smb_url: SMB URL (e.g., 'smb://server/share/path' or '\\server\share\path') (string).
        :param smb_username: Username for SMB authentication (string).
        :param smb_password: Password for SMB authentication (string).
        :param remote_dir: Directory on the remote host to save downloaded files (string, default '/tmp/smb_download').
        :param file_type: File type to filter (e.g., 'rpd') (string, default 'rpd').
        :return: List of downloaded file names with their MD5 sums (list of tuples).
        """
        if not self.check_and_install_smbclient():
            print("Cannot proceed with SMB download due to smbclient issue.")
            return []

        print(SPLIT_LINE)
        print(f"Processing SMB download from {smb_url} to remote directory {remote_dir}...")

        # Process SMB URL
        server, share, download_dir_path, download_filename = self.process_smb_url(smb_url, file_type)
        if server is None:
            return []

        print(f"SERVER   : {server}")
        print(f"SHARE    : {share}")
        print(f"DIR_PATH : {download_dir_path}")
        print(f"FILE_TYPE: {file_type}")
        print(SPLIT_LINE)

        # Create remote directory
        # self.device.execute(f"mkdir -p {remote_dir}")

        # List SMB directory
        dir_listing = self.list_smb_directory(server, share, download_dir_path, smb_username, smb_password)
        if dir_listing is None:
            self.device.execute(f"rm -rf {remote_dir}")
            return []

        print("Directory listing:")
        print(dir_listing)
        print(SPLIT_LINE)

        # Filter files to download
        download_files = self.filter_files_to_download(dir_listing, download_filename, file_type)
        print("Files to download:")
        print("\n".join(download_files) if download_files else "None")
        print(SPLIT_LINE)

        if not download_files:
            print(f"No .{file_type} files found or specified file not available.")
            self.device.execute(f"rm -rf {remote_dir}")
            return []

        # Download files
        downloaded_files = self.download_smb_files(server, share, download_dir_path, download_files, smb_username, smb_password, remote_dir)
        
        print(f"Files downloaded to remote directory {remote_dir}")
        return downloaded_files

if __name__ == "__main__":
    # Example usage
    host = Host(ip="192.168.64.136", username="root", password="a")
    downloaded = host.smb_download_file(
        smb_url='\\\\192.168.65.223\\data\\share\\00_FPGA_OUTPUT\\stargate_asic\\hrdma2\\hrdma_asic_sp_wins_trunk8906_try_fix_lqp_invld.tar',
        smb_username="luoshanguo",
        smb_password="luoshanguo",
        remote_dir="/home/rdma",
        file_type="tar"
    )
    print("Downloaded files with MD5:", downloaded)
    host.device.disconnect()
