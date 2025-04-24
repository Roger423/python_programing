import re

def parse_ib_send_bw(output):
    res = {
        'device': None,
        'qp_num': None,
        'conn_type': None,
        'srq': None,
        'rx_depth': None,
        'mtu': None,
        'rdma_cm_qps': None,
        'data_method': None,
        'local_qpn_list': [],
        'remote_qpn_list': [],
        'bw_result': {}
    }

    lines = output.splitlines()

    for line in lines:
        line = line.strip()

        if match := re.match(r".*Device\s*:\s*(\S+)", line):
            res['device'] = match.group(1).strip()
        elif match := re.match(r"Number of qps\s*:\s*(\d+)", line):
            res['qp_num'] = int(match.group(1))
        elif match := re.match(r"Connection type\s*:\s*(\S+)", line):
            res['conn_type'] = match.group(1)
        # elif match := re.match(r"Using SRQ\s*:\s*(.+)", line):
        #     res['srq'] = match.group(1).strip()
        elif match := re.match(r"Using SRQ\s*:\s*(\S+)", line):
            res['srq'] = match.group(1).strip()
        elif match := re.match(r"RX depth\s*:\s*(\d+)", line):
            res['rx_depth'] = int(match.group(1))
        elif match := re.match(r"Mtu\s*:\s*(\d+)\[B\]", line):
            res['mtu'] = int(match.group(1))
        elif match := re.match(r"rdma_cm QPs\s*:\s*(\S+)", line):
            res['rdma_cm_qps'] = match.group(1)
        elif match := re.match(r"Data ex. method\s*:\s*(\S+)", line):
            res['data_method'] = match.group(1)
        elif match := re.match(r"local address:.*QPN\s+(0x[0-9a-fA-F]+)", line):
            res['local_qpn_list'].append(match.group(1))
        elif match := re.match(r"remote address:.*QPN\s+(0x[0-9a-fA-F]+)", line):
            res['remote_qpn_list'].append(match.group(1))
        elif match := re.match(r"(\d+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", line):
            msg_size = int(match.group(1))
            res['bw_result'][msg_size] = {
                'iterations': int(match.group(2)),
                'bw_peak': float(match.group(3)),
                'bw_avg': float(match.group(4)),
                'msgrate': float(match.group(5))
            }

    return res

# 示例调用
if __name__ == "__main__":
    with open("ib_send_bw_output.txt", "r") as file:
        output_text = file.read()

    parsed_data = parse_ib_send_bw(output_text)
    from pprint import pprint
    pprint(parsed_data)
