import ipaddress
import random
from typing import List
from itertools import islice

def generate_random_ip_segment(mask_length=24):
    """
    Generate a random IPv4 CIDR segment.
    :param mask_length: Subnet mask length. Default is 24.
    :return: Randomly generated IPv4 segment in CIDR notation.
    """
    while True:
        ip_int = random.randint(0, (2 ** 32) - 1)
        seg1 = (ip_int >> 24) & 0xFF
        if seg1 == 127 or seg1 == 0 or seg1 > 223:
            continue
        if mask_length < 32:
            ip_int &= ~((1 << (32 - mask_length)) - 1)
        seg1 = (ip_int >> 24) & 0xFF
        seg2 = (ip_int >> 16) & 0xFF
        seg3 = (ip_int >> 8) & 0xFF
        seg4 = ip_int & 0xFF
        return f'{seg1}.{seg2}.{seg3}.{seg4}/{mask_length}'

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

def generate_mixed_random_ip_segment_list(ip_version_list: list, ipv4_mask_length=24, ipv6_prefix_length=64):
    """
    Generate a list of random IPv4 and IPv6 CIDR segments.
    :param ip_version_list: a list to specify the ip version of each in the segment list.
    :param ipv4_mask_length: IPv4 subnet mask length. Default is 24.
    :param ipv6_prefix_length: IPv6 prefix length. Default is 64.
    :return: List of unique randomly generated IPv4 and IPv6 segments in CIDR notation.
    """
    ip_seg_list = list()
    for ip_ver in ip_version_list:
        if ip_ver == 'ipv4':
            ip_seg = generate_random_ip_segment(mask_length=ipv4_mask_length)
        elif ip_ver == 'ipv6':
            ip_seg = generate_random_ipv6_segment(mask_length=ipv6_prefix_length)
        while ip_seg in ip_seg_list:
            if ip_ver == 'ipv4':
                ip_seg = generate_random_ip_segment(mask_length=ipv4_mask_length)
            elif ip_ver == 'ipv6':
                ip_seg = generate_random_ipv6_segment(mask_length=ipv6_prefix_length)
        ip_seg_list.append(ip_seg)
    return ip_seg_list

def get_random_ip_list_in_segment(ip_segment, ip_count):
    """
    Generate a list of random IPv4 addresses within a specified segment.
    :param ip_segment: IPv4 segment in CIDR notation.
    :param ip_count: Number of IP addresses to generate.
    :return: List of unique IPv4 addresses within the specified segment.
    :raises Exception: If ip_count exceeds the available IPs in the segment.
    """
    network = ipaddress.ip_network(ip_segment, strict=False)
    hosts = list(network.hosts())
    if ip_count > len(hosts):
        raise Exception(f'The IP address count {ip_count} larger than total ip address count {len(hosts)}')
    if ip_count == len(hosts):
        return hosts
    return [str(ipaddr) for ipaddr in random.sample(hosts, ip_count)]

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

def generate_multi_process_ip_list(ip_version_list: List[List[str]]):
    srv_ip_list, clt_ip_list = [], []
    ipver_list = [item for sublist in ip_version_list for item in sublist]
    ip_seg_list = generate_mixed_random_ip_segment_list(ipver_list)

    len_list = [len(sub_list) for sub_list in ip_version_list]
    ip_iter = iter(ip_seg_list)
    splitted_ip_seg_list = [list(islice(ip_iter, sublist_len)) for sublist_len in len_list]

    for i, fc_ip_seg_list in enumerate(splitted_ip_seg_list):
        fc_ipver_list, srv_fc_ip_list, clt_fc_ip_list = ip_version_list[i], [], []
        for j, ip_seg in enumerate(fc_ip_seg_list):
            if fc_ipver_list[j] == 'ipv4':
                get_ip_list_func = get_random_ip_list_in_segment
            elif fc_ipver_list[j] == 'ipv6':
                get_ip_list_func = get_random_ipv6_list_in_segment
            srv_ip, clt_ip = get_ip_list_func(ip_seg, 2)
            srv_fc_ip_list.append(srv_ip)
            clt_fc_ip_list.append(clt_ip)
        srv_ip_list.append(srv_fc_ip_list)
        clt_ip_list.append(clt_fc_ip_list)
    return srv_ip_list, clt_ip_list


if __name__ == "__main__":
    ipver_list = [['ipv4', 'ipv4', 'ipv4'], ['ipv4', 'ipv4', 'ipv4']]
    srv_list, clt_list = generate_multi_process_ip_list(ipver_list)
    print(srv_list)
    print(clt_list)