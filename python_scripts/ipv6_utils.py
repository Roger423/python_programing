import random
import ipaddress


def generate_random_ipv6_list(ip_count):
    """
    Generate a list of random IPv6 addresses with no duplicates.
    :param ip_count: The number of random IPv6 addresses to generate (integer).
    :return: A list of unique IPv6 addresses in compressed string format, within the 2000::/3 range.
    """
    ip_list = set()
    while len(ip_list) < int(ip_count):
        high_bits = random.choice([0x2000, 0x3000]) << 112
        low_bits = random.randint(0, 0xffffffffffffffff)
        ip_int = high_bits | low_bits
        ip_addr = str(ipaddress.IPv6Address(ip_int))
        ip_list.add(ip_addr)
    return list(ip_list)

def generate_random_ipv6_segment(mask_length=64):
    """
    Generate a random IPv6 network segment with the specified prefix length.
    :param mask_length: The prefix length of the network segment (integer, default is 64, range 0-128).
    :return: A random IPv6 network segment in compressed format (e.g., '2000:abcd:1234::/64') within the 2000::/3 range.
    """
    while True:
        segments = [random.choice([0x2000, 0x3000])] + [random.randint(0, 0xffff) for _ in range(7)]
        ip_int = sum(seg << (112 - 16 * i) for i, seg in enumerate(segments))
        if mask_length < 128:
            ip_int &= ~((1 << (128 - mask_length)) - 1)
        try:
            ip_addr = ipaddress.IPv6Address(ip_int)
            network = ipaddress.IPv6Network(f"{ip_addr}/{mask_length}", strict=True)
            return str(network)
        except ValueError:
            continue


def generate_random_ipv6_segment_list(segment_count, mask_length=64):
    """
    Generate a list of random IPv6 network segments with no duplicates.
    :param segment_count: The number of random IPv6 network segments to generate (integer).
    :param mask_length: The prefix length of each network segment (integer, default is 64).
    :return: A list of unique IPv6 network segments in compressed string format.
    """
    ip_seg_list = set()
    while len(ip_seg_list) < segment_count:
        ip_seg = generate_random_ipv6_segment(mask_length=mask_length)
        ip_seg_list.add(ip_seg)
    return list(ip_seg_list)


def get_random_ipv6_list_in_segment(ip_segment, ip_count):
    """
    Generate a list of random IPv6 addresses within a specified network segment.
    :param ip_segment: The IPv6 network segment (string, e.g., '2001:db8::/64').
    :param ip_count: The number of random IPv6 addresses to generate within the segment (integer).
    :return: A list of unique IPv6 addresses in compressed format within the specified segment.
    """
    network = ipaddress.ip_network(ip_segment, strict=False)
    net_int = int(network.network_address)
    mask_length = network.prefixlen
    max_offset = (1 << (128 - mask_length)) - 2
    if ip_count > max_offset:
        raise Exception(f'The IP address count {ip_count} larger than total IP address count {max_offset}')
    ip_list = set()
    while len(ip_list) < ip_count:
        offset = random.randint(1, max_offset)
        ip_int = net_int + offset
        ip_addr = str(ipaddress.IPv6Address(ip_int))
        ip_list.add(ip_addr)
    return list(ip_list)


def get_ipv6_list_from_range(min_ip, max_ip, ip_step):
    """
    Generate a list of IPv6 addresses from a starting IP to an ending IP with a specified step.
    :param min_ip: The starting IPv6 address (string, e.g., '2001:db8::1').
    :param max_ip: The ending IPv6 address (string, e.g., '2001:db8::5').
    :param ip_step: The step value as an IPv6 address (string, e.g., '::1').
    :return: A list of IPv6 addresses in compressed format from min_ip to max_ip with the specified step.
    """
    current_ip = ipaddress.IPv6Address(min_ip)
    max_ip = ipaddress.IPv6Address(max_ip)
    step = int(ipaddress.IPv6Address(ip_step))
    ip_list = []
    while current_ip <= max_ip:
        ip_list.append(str(current_ip))
        current_ip = increment_ipv6(current_ip, step)
    return ip_list


def get_init_ipv6(network_address, prefix_length=64):
    """
    Get the first usable IPv6 address from a network segment (network address + 1).
    :param network_address: The IPv6 network address or segment (string, e.g., '2001:db8::' or '2001:db8::/64').
    :param prefix_length: The prefix length of the network segment (integer, default is 64).
    :return: The first usable IPv6 address in compressed format.
    """
    net_addr = network_address if '/' in network_address else f"{network_address}/{prefix_length}"
    network = ipaddress.IPv6Network(net_addr, strict=False)
    return str(network.network_address + 1)


def increment_ipv6(ip_address, step):
    """
    Increment an IPv6 address by a specified step value.
    :param ip_address: The IPv6 address to increment (string or IPv6Address object).
    :param step: The step value to increment by (integer).
    :return: The incremented IPv6 address as an IPv6Address object.
    """
    ip_int = int(ipaddress.IPv6Address(ip_address))
    next_ip_int = ip_int + step
    return ipaddress.IPv6Address(next_ip_int)


def get_ipv6_increment_step(prefix_length):
    """
    Generate a random IPv6 step value based on the prefix length.
    :param prefix_length: The prefix length determining the step range (integer, range 0-128).
    :return: A random IPv6 step value in compressed string format.
    """
    while True:
        step = [0] * 8
        if prefix_length < 128:
            for i in range(7, -1, -1):
                if prefix_length <= (i * 16):
                    step[i] = random.randint(1, 10)
        if step != [0] * 8:
            break
    step_int = sum(s << (16 * (7 - i)) for i, s in enumerate(step))
    return str(ipaddress.IPv6Address(step_int))


def get_max_ipv6(min_ip, ip_step, ip_num):
    """
    Calculate the maximum IPv6 address given a starting IP, step, and number of addresses.
    :param min_ip: The starting IPv6 address (string, e.g., '2001:db8::1').
    :param ip_step: The step value as an IPv6 address (string, e.g., '::2').
    :param ip_num: The number of addresses to calculate (integer).
    :return: The maximum IPv6 address in compressed format.
    """
    min_ip_int = int(ipaddress.IPv6Address(min_ip))
    step_int = int(ipaddress.IPv6Address(ip_step))
    max_ip_int = min_ip_int + step_int * (ip_num - 1)
    return str(ipaddress.IPv6Address(max_ip_int))


if __name__ == "__main__":
    random_ips = generate_random_ipv6_list(2)
    print("Random IPv6 IPs:", random_ips)

    random_segment = generate_random_ipv6_segment(64)
    print("Random IPv6 Segment:", random_segment)

    random_segment_list = generate_random_ipv6_segment_list(10, 64)
    print("Random IPv6 Segment List:", random_segment_list)

    # segment = "2001:0db8:0000:0000:0000:0000:0000:0000/64"
    segment = "2001:0db8::/64"
    random_ips_in_segment = get_random_ipv6_list_in_segment(segment, 30)
    print(f"Random IPs in {segment}:", random_ips_in_segment)

    min_ip = "2001:0db8::1"
    max_ip = "2001:0db8::5"
    step = "0:0::1"
    ip_range = get_ipv6_list_from_range(min_ip, max_ip, step)
    print(f"IP List from {min_ip} to {max_ip}:", ip_range)

    init_ip = get_init_ipv6("2001:0db8::", 64)
    print("Init IPv6:", init_ip)

    max_ip_calc = get_max_ipv6("2001:0db8::1", "0:0::2", 5)
    print("Max IPv6:", max_ip_calc)
