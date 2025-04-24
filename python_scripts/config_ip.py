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

    def check_interface_connection(self, interface):
        conn_out = self.device.execute("nmcli connection show")
        if interface not in conn_out:
            return False
        out_list = conn_out.splitlines()
        for line in out_list:
            if interface not in line:
                continue
            line_list = line.split()
            uuid_idx = 1
            conn_name = ''
            for i, seg_str in enumerate(line_list):
                if '-' in seg_str:
                    uuid_idx = i
                    conn_name = conn_name.strip()
                    break
                else:
                    conn_name += f'{seg_str} '
            if uuid_idx == 1 and line_list[0] == interface and line_list[-1] == interface:
                return True
            if line_list[-1] == interface and line_list[0] != interface:
                if conn_name != '' and ' ' in conn_name:
                    logger.info(Consts.SPLIT_LINE, also_console=True)
                    logger.info('Delete existing connection with a name not identical to interface name', also_console=True)
                    del_out = self.device.execute(f"nmcli connection delete '{conn_name}'")
                    logger.info(del_out, also_console=True)
                    return False

    def nmcli_add_connection(self, interface):
        add_cmd = f'nmcli connection add con-name {interface} type ethernet ifname {interface}'
        logger.info(Consts.SPLIT_LINE, also_console=True)
        logger.info(f'Add connection for interface {interface} ...', also_console=True)
        add_out = self.device.execute(add_cmd)
        logger.info(f'{self} nmcli add connection output:\n {add_out}', also_console=True)
        return self.check_interface_connection(interface)
    
    def nmcli_delete_connection(self, interface):
        del_cmd = f'nmcli connection delete {interface}'
        logger.info(Consts.SPLIT_LINE, also_console=True)
        logger.info(f'Delete connection for interface {interface} ...', also_console=True)
        add_out = self.device.execute(del_cmd)
        logger.info(f'{self} nmcli delete connection output:\n {add_out}', also_console=True)
        return self.check_interface_connection(interface)

    def nmcli_config_interface_ip(self, interface, ip_addr, mask_length=16, gateway=None, dns=None, ip_version='ipv4'):
        """
        Configure IP (IPv4 or IPv6) for an interface.
        :param ip_version: 'ipv4' or 'ipv6'
        :return: Boolean indicating if configuration was successful
        """
        ck_conn = self.check_interface_connection(interface)
        if not ck_conn:
            self.nmcli_add_connection(interface)
            
        ip_method = 'ipv4' if ip_version.lower() == 'ipv4' else 'ipv6'
        default_mask = 16 if ip_version.lower() == 'ipv4' else 64
        mask = mask_length if mask_length else default_mask
        ip_with_mask = f'{ip_addr}/{mask}'
        
        logger.info(Consts.SPLIT_LINE, also_console=True)
        logger.info(f'nmcli configure {ip_version.upper()} for interface {interface} ...', also_console=True)
        
        conf_cmd = f'nmcli connection modify {interface} {ip_method}.method manual {ip_method}.addresses {ip_with_mask}'
        if gateway:
            conf_cmd += f' {ip_method}.gateway {gateway}'
        if dns:
            conf_cmd += f' {ip_method}.dns "{dns}"'
        
        config_out = self.device.execute(conf_cmd)
        logger.info(config_out, also_console=True)
        
        set_onboot_cmd = f'nmcli connection modify {interface} connection.autoconnect yes'
        config_onboot_out = self.device.execute(set_onboot_cmd)
        logger.info(config_onboot_out, also_console=True)
        
        valid_cmd = f'nmcli connection up {interface}'
        valid_out = self.device.execute(valid_cmd)
        logger.info(valid_out, also_console=True)
        
        if 'successfully activated' not in valid_out.lower():
            logger.error(f'Failed to activate connection for {ip_version.upper()} address {ip_with_mask} on {interface}')
            return False
        
        ip_list = self.get_interface_ip_list(interface, ip_version=ip_version)
        if ip_with_mask not in ip_list:
            logger.error(f'Failed to configure {ip_version.upper()} address {ip_with_mask} on {interface}')
            return False
        
        logger.info(f'Successfully configured {ip_version.upper()} address {ip_with_mask} on {interface}', also_console=True)
        return True

    def nmcli_add_interface_ip(self, interface, ip_addr, mask_length=16, ip_version='ipv4'):
        """
        Add an additional IP (IPv4 or IPv6) to an interface.
        :param ip_version: 'ipv4' or 'ipv6'
        :return: Boolean indicating if addition was successful
        """
        ip_list = self.get_interface_ip_list(interface, ip_version=ip_version)
        default_mask = 16 if ip_version.lower() == 'ipv4' else 64
        mask = mask_length if mask_length else default_mask
        ip_with_mask = f'{ip_addr}/{mask}'
        
        logger.info(Consts.SPLIT_LINE, also_console=True)
        logger.info(f'nmcli add {ip_version.upper()} for interface {interface} ...', also_console=True)
        
        if not ip_list:
            success = self.nmcli_config_interface_ip(interface, ip_addr, mask_length=mask, ip_version=ip_version)
            ip_list = self.get_interface_ip_list(interface, ip_version=ip_version)
            if ip_with_mask not in ip_list:
                logger.error(f'Failed to add {ip_version.upper()} address {ip_with_mask} to {interface}')
                return False
            logger.info(f'Successfully added {ip_version.upper()} address {ip_with_mask} to {interface}', also_console=True)
            return success
        
        ip_method = 'ipv4' if ip_version.lower() == 'ipv4' else 'ipv6'
        add_cmd = f'nmcli connection modify {interface} {ip_method}.method manual +{ip_method}.addresses {ip_with_mask}'
        config_out = self.device.execute(add_cmd)
        logger.info(f'Add interface {ip_version.upper()} output: \n{config_out}', also_console=True)
        
        set_onboot_cmd = f'nmcli connection modify {interface} connection.autoconnect yes'
        config_onboot_out = self.device.execute(set_onboot_cmd)
        logger.info(f'Set interface onboot on output: \n{config_onboot_out}', also_console=True)
        
        valid_cmd = f'nmcli connection up {interface}'
        valid_out = self.device.execute(valid_cmd)
        logger.info(f'Activate interface {ip_version.upper()} output:\n{valid_out}', also_console=True)
        
        if 'successfully activated' not in valid_out.lower():
            logger.error(f'Failed to activate connection after adding {ip_version.upper()} address {ip_with_mask} to {interface}')
            return False
        
        ip_list = self.get_interface_ip_list(interface, ip_version=ip_version)
        if ip_with_mask not in ip_list:
            logger.error(f'Failed to add {ip_version.upper()} address {ip_with_mask} to {interface}')
            return False
        
        logger.info(f'Successfully added {ip_version.upper()} address {ip_with_mask} to {interface}', also_console=True)
        return True

    def _check_ip_exists(self, interface, ip_with_mask, ip_list, ip_version):
        """
        Check if the IP address exists on the interface.
        :param interface: Interface name (e.g., 'ens60')
        :param ip_with_mask: IP with prefix (e.g., '192.168.1.100/24')
        :param ip_list: List of IPs on the interface
        :param ip_version: 'ipv4' or 'ipv6'
        :return: Boolean indicating if the IP exists
        """
        if ip_with_mask not in ip_list:
            logger.info(Consts.SPLIT_LINE, also_console=True)
            logger.error(f'{ip_version.upper()} address {ip_with_mask} not found on interface {interface}')
            return False
        return True

    def _remove_last_ipv4(self, interface):
        """
        Remove the last IPv4 address and switch to auto mode.
        :param interface: Interface name
        """
        logger.info(f'Removing last IPv4 address and switching to auto mode', also_console=True)
        cmd = f'nmcli connection modify {interface} ipv4.method auto ipv4.addresses ""'
        self.device.execute(cmd)

    def _remove_last_ipv6(self, interface):
        """
        Remove the last IPv6 address and disable IPv6.
        :param interface: Interface name
        :return: Boolean indicating if IPv6 was successfully disabled
        """
        logger.info(f'Removing last IPv6 address and disabling IPv6', also_console=True)
        disable_cmd = f'nmcli connection modify {interface} ipv6.method disabled ipv6.addresses ""'
        self.device.execute(disable_cmd)
        
        down_cmd = f'nmcli connection down {interface}'
        self.device.execute(down_cmd)
        
        verify_cmd = f'nmcli connection show {interface} | grep ipv6.method'
        verify_out = self.device.execute(verify_cmd)
        
        if 'disabled' not in verify_out:
            logger.error(f'Failed to set ipv6.method to disabled, aborting')
            return False
        return True

    def _remove_single_ip(self, interface, ip_with_mask, ip_method):
        """
        Remove a single IP address (not the last one).
        :param interface: Interface name
        :param ip_with_mask: IP with prefix
        :param ip_method: 'ipv4' or 'ipv6'
        """
        cmd = f'nmcli connection modify {interface} -{ip_method}.addresses {ip_with_mask}'
        self.device.execute(cmd)

    def _manage_connection_state(self, interface):
        """
        Manage connection state: set autoconnect and handle reactivation.
        :param interface: Interface name
        :return: Boolean indicating if reactivation was needed and successful
        """
        set_onboot_cmd = f'nmcli connection modify {interface} connection.autoconnect yes'
        self.device.execute(set_onboot_cmd)
        
        ipv4_method_cmd = f'nmcli connection show {interface} | grep ipv4.method'
        ipv4_method_out = self.device.execute(ipv4_method_cmd)
        ipv6_method_cmd = f'nmcli connection show {interface} | grep ipv6.method'
        ipv6_method_out = self.device.execute(ipv6_method_cmd)
        ipv4_addresses_cmd = f'nmcli connection show {interface} | grep ipv4.addresses'
        ipv4_addresses_out = self.device.execute(ipv4_addresses_cmd)
        ipv6_addresses_cmd = f'nmcli connection show {interface} | grep ipv6.addresses'
        ipv6_addresses_out = self.device.execute(ipv6_addresses_cmd)
        
        if ('auto' in ipv4_method_out and '--' in ipv4_addresses_out) and ('disabled' in ipv6_method_out and '--' in ipv6_addresses_out):
            logger.info(f'No IP addresses configured (IPv4: auto, IPv6: disabled), skipping reactivation', also_console=True)
            return True
        
        down_cmd = f'nmcli connection down {interface}'
        self.device.execute(down_cmd)
        
        valid_cmd = f'nmcli connection up {interface}'
        self.device.execute(valid_cmd)
        return True

    def _verify_ip_removal(self, interface, ip_with_mask, ip_version):
        """
        Verify that the IP was removed from the interface.
        :param interface: Interface name
        :param ip_with_mask: IP with prefix
        :param ip_version: 'ipv4' or 'ipv6'
        :return: Boolean indicating if removal was successful
        """
        updated_ip_list = self.get_interface_ip_list(interface, ip_version=ip_version)
        success = ip_with_mask not in updated_ip_list
        
        if success:
            logger.info(f'Successfully removed {ip_version.upper()} address {ip_with_mask} from {interface}', also_console=True)
        else:
            logger.error(f'Failed to remove {ip_version.upper()} address {ip_with_mask} from {interface}')
        
        return success

    def nmcli_remove_interface_ip(self, interface, ip_addr, mask_length, ip_version='ipv4'):
        """
        Remove a specific IP (IPv4 or IPv6) address from an interface.
        :param interface: Interface name (e.g., 'ens60')
        :param ip_addr: IP address to remove (e.g., '192.168.1.100' or '2001:db8::100')
        :param mask_length: Prefix length (e.g., 24 for IPv4, 64 for IPv6)
        :param ip_version: 'ipv4' or 'ipv6'
        :return: Boolean indicating if the IP was successfully removed
        """
        ip_with_mask = f'{ip_addr}/{mask_length}'
        ip_method = 'ipv4' if ip_version.lower() == 'ipv4' else 'ipv6'
        ip_list = self.get_interface_ip_list(interface, ip_version=ip_version)
        
        logger.info(Consts.SPLIT_LINE, also_console=True)
        logger.info(f'nmcli remove {ip_version.upper()} address {ip_with_mask} from interface {interface} ...', also_console=True)
        
        if not self._check_ip_exists(interface, ip_with_mask, ip_list, ip_version):
            return False
        
        remaining_ips = [ip for ip in ip_list if ip != ip_with_mask]
        
        if not remaining_ips:
            if ip_version.lower() == 'ipv4':
                self._remove_last_ipv4(interface)
            else:
                if not self._remove_last_ipv6(interface):
                    return False
        else:
            self._remove_single_ip(interface, ip_with_mask, ip_method)
        
        if not self._manage_connection_state(interface):
            return False
        
        return self._verify_ip_removal(interface, ip_with_mask, ip_version)

    def get_interface_ip_list(self, interface, netns=False, ip_version='ipv4'):
        """
        Get the list of IP addresses for an interface.
        :param interface: Interface name (e.g., 'ens60')
        :param netns: Use network namespace (boolean or namespace name, default False)
        :param ip_version: 'ipv4', 'ipv6', or 'all' (default 'ipv4')
        :return: List of IPs (['<addr>/<prefixlen>', ...]) for 'ipv4' or 'ipv6',
                or tuple ([ipv4_list], [ipv6_list]) for 'all'
        """
        if ip_version not in ['ipv4', 'ipv6', 'all']:
            raise ValueError(f"Invalid ip_version: {ip_version}. Must be 'ipv4', 'ipv6', or 'all'.")

        cmd = f"ip addr show {interface}"
        if netns:
            ns_cmd = f"ip netns exec {netns} " if netns is not True else "ip netns exec "
            cmd = ns_cmd + cmd

        output = self.device.execute(cmd)

        ipv4_addresses = []
        ipv6_addresses = []

        for line in output.splitlines():
            line = line.strip()
            if 'inet ' in line and 'scope global' in line:
                addr_part = line.split()[1]
                if '/' in addr_part:
                    ipv4_addresses.append(addr_part)
            elif 'inet6 ' in line and 'scope global' in line:
                addr_part = line.split()[1]
                if '/' in addr_part:
                    ipv6_addresses.append(addr_part)

        if ip_version == 'ipv4':
            return ipv4_addresses
        elif ip_version == 'ipv6':
            return ipv6_addresses
        else:
            return (ipv4_addresses, ipv6_addresses)


if __name__ == "__main__":
    host_ip, host_username, host_passwd, host_interface = '192.168.64.101', 'root', 'a', 'ens60'
    ht = Host(host_ip, host_username, host_passwd)

    # IPv4 configuration
    ht.nmcli_config_interface_ip('ens60', '192.168.1.100', mask_length=24, ip_version='ipv4')
    iface_output = ht.device.execute(f'ifconfig {host_interface}')
    logger.info(iface_output, also_console=True)

    # IPv6 configuration
    ht.nmcli_config_interface_ip('ens60', '2001:db8::100', mask_length=64, ip_version='ipv6')
    iface_output = ht.device.execute(f'ifconfig {host_interface}')
    logger.info(iface_output, also_console=True)

    # Add IPv4 address
    ht.nmcli_add_interface_ip('ens60', '192.168.2.100', mask_length=24, ip_version='ipv4')
    iface_output = ht.device.execute(f'ifconfig {host_interface}')
    logger.info(iface_output, also_console=True)

    # Add IPv6 address
    ht.nmcli_add_interface_ip('ens60', '2001:db8::200', mask_length=64, ip_version='ipv6')
    iface_output = ht.device.execute(f'ifconfig {host_interface}')
    logger.info(iface_output, also_console=True)

    # Remove an IPv4 address
    ht.nmcli_remove_interface_ip('ens60', '192.168.1.100', mask_length=24, ip_version='ipv4')
    iface_output = ht.device.execute(f'ifconfig {host_interface}')
    logger.info(iface_output, also_console=True)

    # Remove the last IPv4 address
    ht.nmcli_remove_interface_ip('ens60', '192.168.2.100', mask_length=24, ip_version='ipv4')
    iface_output = ht.device.execute(f'ifconfig {host_interface}')
    logger.info(iface_output, also_console=True)

    # Remove an IPv6 address
    ht.nmcli_remove_interface_ip('ens60', '2001:db8::100', mask_length=64, ip_version='ipv6')
    iface_output = ht.device.execute(f'ifconfig {host_interface}')
    logger.info(iface_output, also_console=True)

    # Remove the last IPv6 address
    ht.nmcli_remove_interface_ip('ens60', '2001:db8::200', mask_length=64, ip_version='ipv6')
    iface_output = ht.device.execute(f'ifconfig {host_interface}')
    logger.info(iface_output, also_console=True)
