import os
from typing import List
import paramiko
from robot.api import logger


class Consts:
    SPLIT_LINE = '--' * 50

class SSH2Connection:
    def __init__(self, ip: str, username: str, password: str, port: str='22', timeout: int=600) -> None:
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.ssh_conn = paramiko.SSHClient()
        self.ssh_connection()
        
    def ssh_connection(self):
        logger.info(Consts.SPLIT_LINE, also_console=True)
        logger.info(f'SSH connect to {self.ip}...', also_console=True)
        try:
            self.ssh_conn.load_system_host_keys()
            key = paramiko.AutoAddPolicy()
            self.ssh_conn.set_missing_host_key_policy(key)
            self.ssh_conn.connect(self.ip, port=int(self.port), username=self.username, password=self.password, 
                                  timeout=self.timeout)
            return True
        except paramiko.AuthenticationException:
            logger.error("Authentication failed.")
        except paramiko.SSHException as ssh_exception:
            logger.error(f"SSH connection failed: {ssh_exception}")
        return False
    
    def disconnect(self):
        self.ssh_conn.close()

    def execute(self, cmd: str, timeout: int=None):
        _, stdout, stderr = self.ssh_conn.exec_command(cmd, timeout=timeout)
        cmd_stdout = stdout.read().decode('utf-8').strip()
        cmd_stderr = stderr.read().decode('utf-8').strip()
        output = cmd_stdout + "\n" + cmd_stderr if cmd_stderr else cmd_stdout
        return output


class Host:
    def __init__(self, ip: str, username: str, password: str) -> None:
        self.ip = ip
        self.username = username
        self.password = password
        self.device = SSH2Connection(ip=self.ip, username=self.username, password=self.password)
        self.spdk_home = '/opt/spdk'


class NvmePerf:

    def __init__(self, host_dev: Host, rw_list: List[str]=None, bs_list: List[str]=None, iodepth_list: List[str]=None, 
                 cpu_mask: str=None, target_str: str=None, test_paras_list: List[str]=None, test_duration: int=60) -> None:
        self.host_dev = host_dev
        self.rw_list = rw_list
        self.bs_list = bs_list
        self.iodepth_list = iodepth_list
        self.cpu_mask = cpu_mask
        self.target_str = target_str
        self.test_duration = test_duration
        self.test_paras_list = test_paras_list
        self.spdk_home = self.host_dev.spdk_home
        self.spdk_nvme_perf_path = os.path.join(self.spdk_home, 'biuld/bin/spdk_nvme_perf')

    def nvme_perf_test(self):
        if self.test_paras_list:
            for paras in self.test_paras_list:
                rw_type, bs, iodepth = paras.split(':')
                test_cmd = NvmePerfUtils.get_nvme_perf_cmd(self.spdk_nvme_perf_path, rw_type, bs, iodepth, 
                                                           self.test_duration, self.target_str, self.cpu_mask)
                nvme_perf_output = self.host_dev.device.execute(test_cmd)
                logger.info(Consts.SPLIT_LINE, also_console=True)
                logger.info(f"{self.host_dev} execute SPDK nvme_perf with parameters {paras} output:\n" 
                            f"{nvme_perf_output}", also_console=True)


class NvmePerfUtils:

    @staticmethod
    def get_nvme_perf_cmd(spdk_nvme_perf_path: str, rw_type: str, bs: str, iodepth: int, test_duration: int, 
                          target_str: str, cpu_mask: str=None) -> str:
        cmd_parts = [spdk_nvme_perf_path]
        if cpu_mask:
            cmd_parts.append(f"-c {cpu_mask}")
        cmd_parts.extend([f"-q {iodepth}", f"-o {bs}", f"-w {rw_type}", f"-l -t {test_duration}", f"-r {target_str}"])
        return ' '.join(cmd_parts)
    
    @staticmethod
    def parse_nvme_perf_output(nvme_perf_output: str) -> dict:
        pass


if __name__ == "__main__":
    host_ip, host_username, host_passwd, host_interface = '192.168.64.101', 'root', 'a', 'ens60'
    ht = Host(host_ip, host_username, host_passwd)

