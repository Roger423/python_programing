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


if __name__ == "__main__":
    host_ip, host_username, host_passwd, host_interface = '192.168.64.101', 'root', 'a', 'ens60'
    ht = Host(host_ip, host_username, host_passwd)

