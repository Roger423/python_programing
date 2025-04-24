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
        self.pf_map = self.get_pf_map()
    
    def get_pf_map(self):
        pf_map = {}
        get_cmd = f"lspci -D | grep -E -i 'red|xi' | grep -v bridge"
        devices_output = self.device.execute(get_cmd)
        pf_counter = 0
        for dev_line in devices_output.splitlines():
            fc_id = dev_line.split()[0]
            dev_type = self.get_func_type(fc_id)
            if dev_type == "pf":
                pf_idx = f"pf{pf_counter}"
                pf_map[pf_idx] = fc_id
                pf_map[fc_id] = pf_idx
                pf_counter += 1
        return pf_map

    def get_func_type(self, func_id):
        if not func_id.startswith('0000'):
            func_id = f'0000:{func_id}'
        func_type = "pf"
        ck_cmd = f"test -L /sys/bus/pci/devices/{func_id}/physfn && echo yes || echo no"
        ck_output = self.device.execute(ck_cmd)
        if 'yes' in ck_output:
            func_type = "vf"
        return func_type
    
    def get_vf_map(self, pf_func_index=None, pf_func_id=None):
        """
        Get the VF (Virtual Function) mapping for a given PF function ID.
        :param pf_func_index: The PCI function index of the Physical Function (PF), such as pf0, pf1...
        :param pf_func_id: The PCI function ID of the Physical Function (PF)
        :return: Dictionary mapping VF indices (vf0, vf1, ...) to their corresponding function IDs
        """
        if not pf_func_index and not pf_func_id:
            raise Exception("Either pf_func_index or pf_func_id must be provided.")
        if not pf_func_id:
            pf_func_id = self.pf_map.get(pf_func_index)
        vf_map = {}
        if not pf_func_id.startswith('0000'):
            pf_func_id = f'0000:{pf_func_id}'
        vf_cmd = f"ls -l /sys/bus/pci/devices/{pf_func_id}/" + "| awk '/virtfn/ {print $9, $NF}'"
        vf_output = self.device.execute(vf_cmd)
        for vf_line in vf_output.splitlines():
            vf_index_line, vf_id_line = vf_line.split()
            vf_idx, fc_id = f"vf{vf_index_line.strip().replace('virtfn', '')}", vf_id_line.split('/')[-1]
            # print(f"vf_idx --> {vf_idx}")
            # print(f"fc_id --> {fc_id}")
            vf_map[vf_idx] = fc_id
        return vf_map

if __name__ == "__main__":
    from pprint import pprint
    host_ip, user_name, passwd = '192.168.64.136', 'root', 'a'
    ht = Host(host_ip, user_name, passwd)
    # pf_map = ht.get_pf_map()
    print('---------------------------------------')
    print("pf map:")
    pprint(ht.pf_map)
    print('---------------------------------------')
    vf_map = ht.get_vf_map(pf_func_index='pf0')
    print("vf map of pf0:")
    pprint(vf_map)
    print('---------------------------------------')

