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
        try:
            _, stdout, stderr = self.ssh_conn.exec_command(cmd, timeout=timeout)
            cmd_stdout = stdout.read().decode('utf-8').strip()
            cmd_stderr = stderr.read().decode('utf-8').strip()
            if cmd_stderr:
                print(f"Command '{cmd}' returned error: {cmd_stderr}")
            return cmd_stdout
        except paramiko.SSHException as e:
            print(f"Failed to execute command '{cmd}': {str(e)}")
            return ""

class Host:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.device = SSH2Connection(ip=self.ip, username=self.username, password=self.password)

    def get_ibv_devinfo(self, dev_type=None):
        """
        Retrieve and parse the output of `ibv_devinfo` and `rdma link` commands into a dictionary.
        :param dev_type: If None, retrieve all ibv devices; if 'mlx', retrieve mlx devices; if 'rib', retrieve rib devices.
        :return: Dictionary containing parsed device information with netdev mapping.
        """
        ibv_output = self.device.execute("ibv_devinfo")
        if not ibv_output:
            print("No output from ibv_devinfo or command failed.")
            return {}

        rdma_output = self.device.execute("rdma link")
        if not rdma_output:
            print("No output from rdma link or command failed. Netdev mapping will be unavailable.")

        netdev_map = {}
        if rdma_output:
            for line in rdma_output.splitlines():
                line = line.strip()
                match = re.match(r"link (\S+)/(\d+) state (\S+) physical_state (\S+) netdev (\S+)", line)
                if match:
                    dev_name, port, state, phys_state, netdev = match.groups()
                    netdev_map[f"{dev_name}/{port}"] = {
                        "netdev": netdev,
                        "state": state,
                        "physical_state": phys_state
                    }

        devices = {}
        current_device = None
        current_port = None

        for line in ibv_output.splitlines():
            line = line.strip()
            if not line:
                continue

            match_device = re.match(r"hca_id:\s+(\S+)", line)
            if match_device:
                current_device = match_device.group(1)
                if dev_type and not current_device.startswith(dev_type):
                    current_device = None
                    current_port = None
                    continue
                devices[current_device] = {"ports": {}}
                current_port = None
                continue

            match_port = re.match(r"port:\s+(\d+)", line)
            if match_port and current_device:
                current_port = match_port.group(1)
                devices[current_device]["ports"][current_port] = {}
                dev_port_key = f"{current_device}/{current_port}"
                if dev_port_key in netdev_map:
                    devices[current_device]["ports"][current_port].update(netdev_map[dev_port_key])
                continue

            match_key_value = re.match(r"(\S+):\s+(.+)", line)
            if match_key_value and current_device:
                key, value = match_key_value.groups()
                if key in ["max_mtu", "active_mtu"]:
                    value = value.split()[0]
                if current_port:
                    devices[current_device]["ports"][current_port][key] = value
                else:
                    devices[current_device][key] = value

        return devices

    def display_ibv_devinfo(self, devices, dev_type=None):
        """
        Display selected fields from the provided IBV devices dictionary.
        :param devices: Dictionary of IBV device information (from get_ibv_devinfo).
        :param dev_type: Optional label for display purposes (e.g., 'mlx', 'rib', or None for 'all').
        """
        if not devices:
            print("No devices provided to display.")
            return

        display_fields = ["node_guid", "active_mtu", "link_layer", "max_mtu", "netdev", "physical_state"]

        print(SPLIT_LINE)
        print(f"Displaying IBV devices (type: {dev_type or 'all'})")
        print(SPLIT_LINE)

        for dev_name, dev_info in devices.items():
            print(f"Device: {dev_name}")
            # Display device-level fields
            for field in display_fields:
                if field in dev_info and field not in ["netdev", "physical_state"]:  # These are port-specific
                    print(f"  {field}: {dev_info[field]}")

            # Display port-level fields
            for port_num, port_info in dev_info["ports"].items():
                print(f"  Port {port_num}:")
                for field in display_fields:
                    if field in port_info:
                        print(f"    {field}: {port_info[field]}")
                if not any(field in port_info for field in display_fields):
                    print("    No relevant fields available.")
            print()

if __name__ == "__main__":
    host_ip, user_name, passwd = '192.168.64.136', 'root', 'a'
    ht = Host(host_ip, user_name, passwd)
    
    # Get device info once and reuse
    all_devices = ht.get_ibv_devinfo()
    mlx_devices = ht.get_ibv_devinfo("mlx")
    rib_devices = ht.get_ibv_devinfo("rib")

    print("All devices:")
    ht.display_ibv_devinfo(all_devices)
    
    print("MLX devices:")
    ht.display_ibv_devinfo(mlx_devices, "mlx")
    
    print("RIB devices:")
    ht.display_ibv_devinfo(rib_devices, "rib")
    
    ht.device.disconnect()
