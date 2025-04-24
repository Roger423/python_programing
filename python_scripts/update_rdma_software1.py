import paramiko
import time
from pexpect import pxssh
import sys

SPLIT_LINE = '-' * 80
RQOS_DEP_PKG_LIST = ["yaml-cpp", "yaml-cpp-devel", "yaml-cpp-static"]
TIME_STR = time.strftime("%Y%m%d_%H%M%S")

class SSH2Connection:
    def __init__(self, ip, username, password, port='22', timeout=600):
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.ssh_conn = paramiko.SSHClient()
        self.ssh_connection()

    def ssh_connection(self):
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
        self.ssh_conn.close()

    def execute(self, cmd, timeout=None):
        _, stdout, stderr = self.ssh_conn.exec_command(cmd, timeout=timeout)
        cmd_stdout = stdout.read().decode('utf-8').strip()
        cmd_stderr = stderr.read().decode('utf-8').strip()
        output = cmd_stdout + "\n" + cmd_stderr if cmd_stderr else cmd_stdout
        return output

class Host:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.device = SSH2Connection(ip=self.ip, username=self.username, password=self.password)
        self.px_ssh = pxssh.pxssh(timeout=3600)  # Global timeout of 1 hour

    def pxssh_login(self):
        try:
            self.px_ssh.login(self.ip, self.username, self.password)
            print(f"pxssh logged in to {self.ip} successfully")
            return True
        except pxssh.ExceptionPxssh as e:
            print(f"pxssh login failed: {str(e)}")
            return False

    def pxssh_logout(self):
        self.px_ssh.logout()
        print("pxssh logged out")

    def install_dep_pkgs(self, pkg_list):
        print(f'Install dependencies: {pkg_list}')
        for pkg in pkg_list:
            check_cmd = f"rpm -q {pkg} &> /dev/null && echo 'installed' || echo 'not installed'"
            result = self.device.execute(check_cmd)
            if "installed" in result:
                print(f'{pkg} has already been installed')
                continue
            print(f"Installing {pkg}...")
            install_cmd = f"sudo yum install -y {pkg}"
            install_result = self.device.execute(install_cmd)
            if "error" in install_result.lower() or "failed" in install_result.lower():
                print(f"{pkg} installation failed: {install_result}")
            else:
                print(f"{pkg} installed successfully")

    def check_and_install_expect(self):
        expect_check = self.device.execute("command -v expect &> /dev/null && echo 'installed' || echo 'not installed'")
        if "not installed" in expect_check:
            print("Expect is not installed. Installing expect...")
            install_expect = self.device.execute("sudo yum install -y expect")
            if "error" in install_expect.lower() or "failed" in install_expect.lower():
                print(f"Failed to install expect: {install_expect}")
                return False
        return True

    def backup_rdma_software(self, rdma_software_name, rdma_root_dir='/home/rdma'):
        rdma_sw_path = f"{rdma_root_dir}/{rdma_software_name}"
        bak_sw_path = f"{rdma_root_dir}/{rdma_software_name}_bak_{TIME_STR}"
        print(f'Backing up {rdma_software_name} from {rdma_sw_path} to {bak_sw_path}')
        check_dir_cmd = f"test -d {rdma_sw_path} && echo 'exists' || echo 'not found'"
        dir_exists = self.device.execute(check_dir_cmd)
        if "exists" in dir_exists:
            print(f"Backing up existing {rdma_software_name} directory ...")
            backup_cmd = f"mv {rdma_sw_path} {bak_sw_path}"
            backup_result = self.device.execute(backup_cmd)
            if "error" in backup_result.lower() or "failed" in backup_result.lower():
                print(f"Backup failed: {backup_result}")
                return False
        return True

    def download_rdma_software(self, software_name, git_username, git_password, gitlab_addr, project, 
                               rdma_root_dir="/home/rdma"):
        rdma_sw_path = f"{rdma_root_dir}/{software_name}"
        print(f"Downloading new {software_name} ...")
        git_clone_cmd = f"git clone http://{git_username}:{git_password}@{gitlab_addr}/{project}/{software_name}.git"
        clone_result = self.device.execute(f'cd {rdma_root_dir} && {git_clone_cmd}')
        if "fatal" in clone_result.lower() or "error" in clone_result.lower():
            print(f"Failed to download {software_name}: {clone_result}")
            return False
        ck_download_cmd = f"test -d {rdma_sw_path} && echo 'exists' || echo 'not found'"
        download_result = self.device.execute(ck_download_cmd)
        if "exists" in download_result:
            print(f"Downloaded new {software_name} successfully")
            return True
        print(f"Download of new {software_name} failed")
        return False

    def update_submodules(self, git_username, git_password, gitlab_addr, repo_path):
        """
        Update submodules for a given repository path using pxssh.
        :param git_username: GitLab username (string).
        :param git_password: GitLab password or token (string).
        :param gitlab_addr: GitLab server address (string).
        :param repo_path: Path to the repository on the remote host (string).
        :return: True if submodules updated successfully, False otherwise.
        """
        print(f"Updating submodules for repository at {repo_path} ...")
        if not self.pxssh_login():
            return False

        try:
            self.px_ssh.sendline(f"cd {repo_path} && git submodule update --init --recursive")
            while True:
                index = self.px_ssh.expect([
                    "Username for 'http://.*':",           # Git username prompt
                    "Password for 'http://.*':",           # Git password prompt
                    self.px_ssh.PROMPT,                    # Shell prompt (command completed)
                    pxssh.TIMEOUT                          # Timeout
                ], timeout=300)  # Per-expect timeout of 5 minutes

                if index == 0:
                    print("Providing Git username...")
                    self.px_ssh.sendline(git_username)
                elif index == 1:
                    print("Providing Git password...")
                    self.px_ssh.sendline(git_password)
                elif index == 2:
                    output = self.px_ssh.before.decode('utf-8')
                    if "fatal" in output.lower() or "error" in output.lower():
                        print(f"Submodule update failed: {output}")
                        self.pxssh_logout()
                        return False
                    print("Submodule update completed successfully")
                    break
                elif index == 3:
                    print(f"Timed out waiting for submodule update: {self.px_ssh.before.decode('utf-8')}")
                    self.pxssh_logout()
                    return False

        except pxssh.ExceptionPxssh as e:
            print(f"pxssh encountered an error: {str(e)}")
            self.pxssh_logout()
            return False

        self.pxssh_logout()
        return True

    def update_rqos(self, git_username, git_password, gitlab_addr, project, rqos_branch='main', 
                    rdma_root_dir="/home/rdma"):
        """
        Update rqos on the remote host.
        :param git_username: GitLab username (string).
        :param git_password: GitLab password or token (string).
        :param gitlab_addr: GitLab server address (string).
        :param project: GitLab project name (string).
        :param rqos_branch: rqos branch to checkout (string, default 'main').
        :param rdma_root_dir: Root directory for RDMA operations (string, default '/home/rdma').
        :return: True if update is successful, False otherwise.
        """
        print(SPLIT_LINE)

        # Install dependencies
        self.install_dep_pkgs(RQOS_DEP_PKG_LIST)

        # Check and install expect
        if not self.check_and_install_expect():
            return False

        # Backup existing rqos
        if not self.backup_rdma_software('rqos', rdma_root_dir=rdma_root_dir):
            return False

        # Download rqos
        if not self.download_rdma_software('rqos', git_username, git_password, gitlab_addr, project, 
                                           rdma_root_dir=rdma_root_dir):
            return False

        rqos_path = f"{rdma_root_dir}/rqos"

        # Change branch
        print(f"Changing rqos branch to {rqos_branch}")
        checkout_cmd = f"cd {rqos_path} && git checkout {rqos_branch}"
        checkout_result = self.device.execute(checkout_cmd)
        if "error" in checkout_result.lower():
            print(f"Failed to checkout branch {rqos_branch}: {checkout_result}")
            return False
        print("Current branches:")
        print(self.device.execute(f"cd {rqos_path} && git branch"))

        # Update submodules
        if not self.update_submodules(git_username, git_password, gitlab_addr, rqos_path):
            return False

        # Compile rqos
        print("Compiling new rqos ...")
        compile_cmd = f"cd {rqos_path} && make && make install"
        compile_result = self.device.execute(compile_cmd, timeout=600)
        if "error" in compile_result.lower() or "failed" in compile_result.lower():
            print(f"Compile rqos failed: {compile_result}")
            return False
        print("Compile rqos success!")

        print(SPLIT_LINE)
        return True

if __name__ == "__main__":
    host = Host(ip="192.168.64.136", username="root", password="a")
    success = host.update_rqos(
        git_username='luoshanguo',
        git_password='lsg00510223',
        gitlab_addr='192.168.65.225',
        project='c3000',
        rqos_branch='main',
        rdma_root_dir="/home/rdma"
    )
    print(f"rqos update successful: {success}")
    host.device.disconnect()
