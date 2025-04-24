import paramiko
import re

SPLIT_LINE = '-' * 80

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

    def get_ibv_devinfo(self, dev_type=None):
        """
        Retrieve and parse the output of the `ibv_devinfo` command into a dictionary.
        :param dev_type: If None, retrieve all ibv devices; if 'mlx', retrieve mlx devices; if 'rib', retrieve rib devices.
        :return: Dictionary containing parsed device information.
        """
        output = self.device.execute("ibv_devinfo")
        if not output:
            print("Failed to retrieve ibv_devinfo output.")
            return {}

        devices = {}
        current_device = None
        port_id = None

        for line in output.splitlines():
            line = line.strip()

            match_device = re.match(r"hca_id:\s+(\S+)", line)
            if match_device:
                current_device = match_device.group(1)
                if dev_type and not current_device.startswith(dev_type):
                    current_device = None
                    port_id = None
                    continue
                devices[current_device] = {}
                port_id = None  # Reset port_id for new device
                continue

            match_port = re.match(r"port:\s+(\d+)", line)
            if match_port and current_device:
                port_id = f"port_{match_port.group(1)}"
                devices[current_device][port_id] = {}
                continue

            match_key_value = re.match(r"(\S+):\s+(.+)", line)
            if match_key_value and current_device:
                key, value = match_key_value.groups()
                
                if key in ["max_mtu", "active_mtu"]:
                    value = value.split()[0]  # Keep only the numeric part
                
                if port_id:
                    devices[current_device].setdefault(port_id, {})[key] = value
                else:
                    devices[current_device][key] = value

        return devices


if __name__ == "__main__":
    from pprint import pprint
    host_ip, user_name, passwd = '192.168.64.136', 'root', 'a'
    ht = Host(host_ip, user_name, passwd)
    
    print('---------------------------------------')
    print("All devices:")
    pprint(ht.get_ibv_devinfo())
    
    print('---------------------------------------')
    print("MLX devices:")
    pprint(ht.get_ibv_devinfo("mlx"))
    
    print('---------------------------------------')
    print("RIB devices:")
    pprint(ht.get_ibv_devinfo("rib"))
    print('---------------------------------------')
