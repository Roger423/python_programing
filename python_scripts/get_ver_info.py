import paramiko


SPLIT_LINE = '-' * 80

class SSH2Connection():

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

    def get_version_info(self):
        cmd = "rft version"
        output = self.device.execute(cmd)
        version_info = {}
        section = None
        for line in output.split('\n'):
            line = line.strip()
            if line.endswith('INFO'):
                section = line.replace(' INFO', '').lower()
                version_info[section] = {}
            elif ':' in line and section:
                key, value = map(str.strip, line.split(':', 1))
                version_info[section][key.replace(' ', '_').lower()] = value
        return version_info


if __name__ == "__main__":
    from pprint import pprint
    host_ip, user_name, passwd = '192.168.64.136', 'root', 'a'
    ht = Host(host_ip, user_name, passwd)
    # pf_map = ht.get_pf_map()
    print('---------------------------------------')
    print("version info:")
    pprint(ht.get_version_info())
    print('---------------------------------------')
