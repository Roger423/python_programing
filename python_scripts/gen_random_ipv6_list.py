import random
import ipaddress

import ipaddress
import random

def generate_random_ipv6_list(ip_count, prefix_length=64):
    """
    Generate a list of random IPv6 addresses with no duplicates in the same randomly generated subnet.

    :param ip_count: Number of IPv6 addresses to generate.
    :param prefix_length: Prefix length (default: 64).
    :return: List of IPv6 addresses in compressed string format with prefix length.
    """
    if prefix_length > 64:
        raise ValueError("Prefix length > 64 not supported for this generator.")

    # Generate a random /prefix_length network in 2000::/3
    while True:
        # Generate a random address in 2000::/3 range
        random_16bit_prefix = random.randint(0x2000, 0x3fff)
        random_segments = [random_16bit_prefix] + [random.randint(0, 0xffff) for _ in range((prefix_length // 16) - 1)]
        prefix_str = ':'.join(f"{seg:x}" for seg in random_segments)
        try:
            network = ipaddress.IPv6Network(f"{prefix_str}::/{prefix_length}", strict=False)
            break
        except ipaddress.AddressValueError:
            continue

    # Generate unique IPs in this network
    ip_list = set()
    while len(ip_list) < int(ip_count):
        rand_ip = ipaddress.IPv6Address(network.network_address + random.randint(1, network.num_addresses - 2))
        ip_list.add(f"{rand_ip}/{prefix_length}")

    return list(ip_list)



# 示例：
print(generate_random_ipv6_list(5))

