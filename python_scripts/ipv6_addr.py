import random
import ipaddress

def generate_random_ipv6_address_list(ipv6_address_count):
    """
    Generate a list of random IPv6 addresses.
    :param ipv6_address_count: Number of IPv6 addresses to generate.
    :return: List of unique randomly generated IPv6 addresses.
    """
    ipv6_address_list = []
    while len(ipv6_address_list) < ipv6_address_count:
        ipv6_segments = [f"{random.randint(0, 0xFFFF):x}" for _ in range(8)]
        ipv6_address = ":".join(ipv6_segments)
        if ipv6_address not in ipv6_address_list:
            ipv6_address_list.append(ipv6_address)
    return ipv6_address_list

def generate_random_ipv6_subnet(prefix_length=64):
    """
    Generate a random IPv6 subnet.
    :param prefix_length: The prefix length for the subnet. Default is 64.
    :return: A random IPv6 subnet in CIDR notation (e.g., "2001:db8::/64").
    """
    ipv6_segments = [f"{random.randint(0, 0xFFFF):x}" for _ in range(4)]
    ipv6_subnet = ":".join(ipv6_segments) + "::/" + str(prefix_length)
    return ipv6_subnet

def generate_random_ipv6_subnet_list(subnet_count, prefix_length=64):
    """
    Generate a list of random IPv6 subnets.
    :param subnet_count: Number of IPv6 subnets to generate.
    :param prefix_length: The prefix length for the subnet. Default is 64.
    :return: List of unique IPv6 subnets in CIDR notation.
    """
    ipv6_subnet_list = []
    while len(ipv6_subnet_list) < subnet_count:
        ipv6_subnet = generate_random_ipv6_subnet(prefix_length=prefix_length)
        if ipv6_subnet not in ipv6_subnet_list:
            ipv6_subnet_list.append(ipv6_subnet)
    return ipv6_subnet_list

def get_random_ipv6_addresses_in_subnet(ipv6_subnet, address_count):
    """
    Generate random IPv6 addresses within a specified subnet.
    :param ipv6_subnet: The IPv6 subnet in CIDR notation (e.g., "2001:db8::/64").
    :param address_count: Number of IPv6 addresses to generate.
    :return: List of randomly generated IPv6 addresses within the subnet.
    :raises Exception: If address_count exceeds the number of available addresses in the subnet.
    """
    network = ipaddress.ip_network(ipv6_subnet, strict=False)
    if address_count > network.num_addresses - 2:  # Excluding network and broadcast addresses
        raise Exception(f"The address count {address_count} is larger than available addresses in the subnet.")
    
    ipv6_address_set = set()
    while len(ipv6_address_set) < address_count:
        random_ipv6_int = random.randint(int(network.network_address) + 1, int(network.broadcast_address) - 1)
        random_ipv6_address = ipaddress.IPv6Address(random_ipv6_int)
        ipv6_address_set.add(str(random_ipv6_address))
    return list(ipv6_address_set)

def increment_ipv6_address(ipv6_address, step_size):
    """
    Increment an IPv6 address by a specified step.
    :param ipv6_address: The starting IPv6 address (e.g., "2001:db8::1").
    :param step_size: The step size as an IPv6 address (e.g., "0:0:0:0:0:1:0:0").
    :return: The incremented IPv6 address.
    """
    ipv6_address_int = int(ipaddress.IPv6Address(ipv6_address))
    step_size_int = int(ipaddress.IPv6Address(step_size))
    incremented_ipv6_int = ipv6_address_int + step_size_int
    return str(ipaddress.IPv6Address(incremented_ipv6_int))

def get_initial_ipv6_address(network_address, prefix_length=64):
    """
    Get the initial usable IPv6 address within a subnet.
    :param network_address: The network address in CIDR notation (e.g., "2001:db8::").
    :param prefix_length: The prefix length for the subnet. Default is 64.
    :return: The initial usable IPv6 address in the subnet.
    """
    net_addr = network_address if '/' in network_address else f"{network_address}/{prefix_length}"
    network = ipaddress.IPv6Network(net_addr, strict=False)
    return str(network.network_address + 1)

def get_maximum_ipv6_address(start_ipv6_address, step_size, step_count):
    """
    Calculate the maximum IPv6 address reachable with the given step and count.
    :param start_ipv6_address: The starting IPv6 address (e.g., "2001:db8::1").
    :param step_size: The step size as an IPv6 address (e.g., "0:0:0:0:0:1:0:0").
    :param step_count: Number of steps to increment.
    :return: The maximum IPv6 address reachable.
    """
    start_ipv6_int = int(ipaddress.IPv6Address(start_ipv6_address))
    step_size_int = int(ipaddress.IPv6Address(step_size))
    maximum_ipv6_int = start_ipv6_int + step_size_int * (step_count - 1)
    return str(ipaddress.IPv6Address(maximum_ipv6_int))

if __name__ == "__main__":
    random_ips = generate_random_ipv6_address_list(3)
    print("Random IPv6 IPs:", random_ips)

    random_segment = generate_random_ipv6_subnet(64)
    print("Random IPv6 Segment:", random_segment)

    random_segment_list = generate_random_ipv6_subnet_list(2, 64)
    print("Random IPv6 Segment List:", random_segment_list)

    segment = "2001:0db8:0000:0000:0000:0000:0000:0000/64"
    random_ips_in_segment = get_random_ipv6_addresses_in_subnet(segment, 3)
    print(f"Random IPs in {segment}:", random_ips_in_segment)

    min_ip = "2001:0db8:0000:0000:0000:0000:0000:0001"
    max_ip = "2001:0db8:0000:0000:0000:0000:0000:0005"
    step = "0:0:0:0:0:0:0:1"
    # ip_range = get_ipv6_list_from_range(min_ip, max_ip, step)
    # print(f"IP List from {min_ip} to {max_ip}:", ip_range)

    init_ip = get_initial_ipv6_address("2001:0db8:0000:0000:0000:0000:0000:0000", 64)
    print("Init IPv6:", init_ip)

    max_ip_calc = get_maximum_ipv6_address("2001:0db8:0000:0000:0000:0000:0000:0001", "0:0:0:0:0:0:0:2", 5)
    print("Max IPv6:", max_ip_calc)
