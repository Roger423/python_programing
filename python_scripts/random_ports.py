import random
from typing import List
from itertools import islice


def generate_random_ports(count):
    """
    Generate a list of random TCP/UDP port numbers, avoiding reserved and common well-known ports.
    :param count: Number of ports to generate
    :return: A list of unique, random port numbers
    """
    if count > 65535 - 1025:
        raise ValueError("Requested number of ports exceeds the available port range.")
    reserved_ports = set(range(0, 1025))
    well_known_ports = {
        22, 21, 25, 80, 110, 123, 143, 161, 389, 443,    # Common services
        2049, 2379, 2380, 3306, 5432, 6379, 8080, 8443,
        9092, 9200, 9300, 27017, 5000, 5001, 8888, 8000
    }
    blacklist_ports = reserved_ports.union(well_known_ports)
    available_ports = list(set(range(1025, 65536)) - blacklist_ports)
    if count > len(available_ports):
        raise ValueError("Requested number of ports exceeds the number of available ports.")
    return random.sample(available_ports, count)


def generate_multi_process_port_list(ip_version_list: List[List[str]]):
    ipver_list = [item for sublist in ip_version_list for item in sublist]
    port_list = generate_random_ports(len(ipver_list))
    len_list = [len(sub_list) for sub_list in ip_version_list]
    return [list(islice(iter(port_list), sublist_len)) for sublist_len in len_list]


if __name__ == "__main__":
    ipver_list = [['ipv4', 'ipv4', 'ipv4'], ['ipv4', 'ipv4', 'ipv4']]
    port_list = generate_multi_process_port_list(ipver_list)
    print(port_list)
