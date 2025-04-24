import paramiko
import time
import pexpect

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
    
    def execute_live_print(self, cmd, timeout=None):
        _, stdout, stderr = self.ssh_conn.exec_command(cmd, timeout=timeout, get_pty=True)
        output = ''
        while True:
            output_line = stdout.readline()
            output += output_line
            print(output_line)
            if stdout.channel.exit_status_ready():
                remain_output = stdout.read().decode()
                output += remain_output
                print(remain_output)
                break
        cmd_stderr = stderr.read().decode('utf-8').strip()
        if cmd_stderr:
            print(cmd_stderr)
            output = output + '\n' + cmd_stderr
        return output


class Host:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.device = SSH2Connection(ip=self.ip, username=self.username, password=self.password)
        self.pf_map = {}

    def intall_dep_pkgs(self, pkg_list):
        print(f'Install dependencies for rdma-core: {pkg_list}')
        for pkg in pkg_list:
            check_cmd = f"rpm -q {pkg} &> /dev/null && echo 'installed' || echo 'not installed'"
            result = self.device.execute(check_cmd)
            if "installed" in result:
                print(f'{pkg} has already installed')
                continue
            print(f"Install {pkg}...")
            install_cmd = f"sudo yum install -y {pkg}"
            install_result = self.device.execute(install_cmd)
            if "error" in install_result.lower() or "failed" in install_result.lower():
                print(f"{pkg} installed failed: {install_result}")
            else:
                print(f"{pkg} installed successful")

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
        print(f'Backup {rdma_software_name} from {rdma_sw_path} to {bak_sw_path}')
        check_dir_cmd = f"test -d {rdma_sw_path} && echo 'exists' || echo 'not found'"
        dir_exists = self.device.execute(check_dir_cmd)
        if "exists" in dir_exists:
            print(f"Backup existing {rdma_software_name} directory ...")
            backup_cmd = f"mv {rdma_sw_path} {bak_sw_path}"
            backup_result = self.device.execute(backup_cmd)
            if "error" in backup_result.lower() or "failed" in backup_result.lower():
                print(f"Backup failed: {backup_result}")
                return False
        return True
    
    def download_rdma_software(self, software_name, git_username, git_password, gitlab_addr, project, 
                               rdma_root_dir="/home/rdma"):
        rdma_sw_path = f"{rdma_root_dir}/{software_name}"
        print(f"Download new {software_name} ...")
        git_clone_cmd = f"git clone http://{git_username}:{git_password}@{gitlab_addr}/{project}/{software_name}.git"
        clone_result = self.device.execute(f'cd {rdma_root_dir} && {git_clone_cmd}')
        if "fatal" in clone_result.lower() or "error" in clone_result.lower():
            print(f"Failed to download {software_name}: {clone_result}")
            return False
        ck_download_cmd = f"test -d {rdma_sw_path} && echo 'exists' || echo 'not found'"
        download_result = self.device.execute(ck_download_cmd)
        if "exists" in download_result:
            print(f"Download new {software_name} successful")
        else:
            print(f"Download new {software_name} failed")
            return False
        return True

    def update_rqos(self, git_username, git_password, gitlab_addr, project, rqos_branch='main',
                    rdma_root_dir="/home/rdma"):
        print(SPLIT_LINE)
        self.intall_dep_pkgs(RQOS_DEP_PKG_LIST)
        print(SPLIT_LINE)
        self.check_and_install_expect()
        
        rqos_path = f"{rdma_root_dir}/rqos"
        self.backup_rdma_software('rqos', rdma_root_dir=rdma_root_dir)
        
        dld_res = self.download_rdma_software('rqos', git_username, git_password, gitlab_addr, project,
                                            rdma_root_dir=rdma_root_dir)
        if not dld_res:
            return False

        print(f"Change rqos branch to {rqos_branch}")
        checkout_cmd = f"git checkout {rqos_branch}"
        checkout_result = self.device.execute(f'cd {rqos_path} && {checkout_cmd}')
        if "error" in checkout_result.lower():
            print(f"Failed to checkout branch {rqos_branch}: {checkout_result}")
            return False

        print(self.device.execute(f'cd {rqos_path} && git branch'))

        print("Download submodules for rqos ...")

        # 这里用 pexpect 来处理交互式 git submodule update
        try:
            child = pexpect.spawn(f'git submodule update --init --recursive', cwd=rqos_path, timeout=120)

            while True:
                index = child.expect([
                    r'Username for .*:', 
                    r'Password for .*:', 
                    pexpect.EOF,  # 命令结束
                    pexpect.TIMEOUT
                ], timeout=60)

                if index == 0:
                    print("Providing username...")
                    child.sendline(git_username)
                elif index == 1:
                    print("Providing password...")
                    child.sendline(git_password)
                elif index == 2:
                    print("Submodule update completed.")
                    break
                elif index == 3:
                    print("Timed out waiting for submodule update")
                    return False

        except pexpect.exceptions.ExceptionPexpect as e:
            print(f"pexpect encountered an error: {str(e)}")
            return False

        print("Compile new rqos ...")
        make_result = self.device.execute(f'cd {rqos_path} && make && make install && \
                                        echo "compile rqos success" || echo "compile rqos failed"')
        if "compile rqos failed" in make_result.lower():
            print(f"Compile rqos failed: {make_result}")
            return False

        print("Compile rqos success!")
        print(SPLIT_LINE)
        return True


if __name__ == "__main__":
    host = Host(ip="192.168.64.136", username="root", password="a")
    # Example usage for each method
    host.update_rqos('luoshanguo', 'lsg00510223', '192.168.65.225', 'c3000', rqos_branch='main', 
                     rdma_root_dir="/home/rdma")
    host.device.disconnect()
