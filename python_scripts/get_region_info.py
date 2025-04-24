import re
import paramiko
from robot.api import logger


class Consts:
    SPLIT_LINE = '--' * 50

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

    def get_region_info(self):
        output = self.device.execute("rft region -a")
        lines = output.splitlines()
        result = {
            'total': {},
            'function_info': {}
        }
        for line in lines:
            line = line.strip()
            if match := re.match(r"function total:\s+(\d+)", line):
                result['total']['function_total'] = int(match.group(1))
            elif match := re.match(r"region total:\s+(\d+)", line):
                result['total']['region_total'] = int(match.group(1))
            elif match := re.match(r"(\w+)_per_region_num:\s+(\d+)", line):
                result['total'][match.group(1) + '_per_region_num'] = int(match.group(2))
            # elif match := re.match(r"\[BDF ([^\]]+)\] function\[(\d+)\] region number: (\d+)", line):
            #     bdf = f"0000:{match.group(1)}"
            #     region_num = int(match.group(3))
            #     result['function_info'][int(match.group(2))] = {
            #         'func_id': bdf,
            #         'region_num': region_num
            #     }
            elif match := re.search(r"\[BDF ([^\]]+)\] function\[(\d+)\] region number: (\d+)", line):
                bdf = f"0000:{match.group(1)}"
                region_num = int(match.group(3))
                result['function_info'][int(match.group(2))] = {
                    'func_id': bdf,
                    'region_num': region_num
                }
        return result


if __name__ == "__main__":
    host_ip, host_username, host_passwd, host_interface = '192.168.64.101', 'root', 'a', 'ens60'
    ht = Host(host_ip, host_username, host_passwd)
    region_info = ht.get_region_info()
    # logger.info(region_info, also_console=True)
    from pprint import pprint
    pprint(region_info)

