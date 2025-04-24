import re


output = """
[root@localhost rdma]# ib_send_bw -a -R -d rib_0 --report_gbits -F
 WARNING: BW peak won't be measured in this run.

************************************
* Waiting for client to connect... *
************************************
---------------------------------------------------------------------------------------
                    Send BW Test
 Dual-port       : OFF          Device         : rib_0
 Number of qps   : 1            Transport type : IB
 Connection type : RC           Using SRQ      : OFF
 PCIe relax order: ON
 ibv_wr* API     : OFF
 RX depth        : 512
 CQ Moderation   : 100
 Mtu             : 4096[B]
 Link type       : Ethernet
 GID index       : 1
 Max inline data : 0[B]
 rdma_cm QPs     : ON
 Data ex. method : rdma_cm
---------------------------------------------------------------------------------------
 Waiting for client rdma_cm QP to connect
 Please run the same command with the IB/RoCE interface IP
---------------------------------------------------------------------------------------
 local address: LID 0000 QPN 0x000b PSN 0x1562f0
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:00:01
 remote address: LID 0000 QPN 0x000b PSN 0xb1d358
 GID: 00:00:00:00:00:00:00:00:00:00:255:255:10:00:00:02
---------------------------------------------------------------------------------------
 #bytes     #iterations    BW peak[Gb/sec]    BW average[Gb/sec]   MsgRate[Mpps]
 2          1000           0.000000            0.045614            2.850856
 4          1000           0.000000            0.090209            2.819047
 8          1000             0.00               0.18                 2.822587
 16         1000             0.00               0.36                 2.789820
 32         1000             0.00               0.70                 2.753321
 64         1000             0.00               1.43                 2.802276
 128        1000             0.00               2.89                 2.820442
 256        1000             0.00               5.68                 2.772903
 512        1000             0.00               11.08                2.705823
 1024       1000             0.00               22.64                2.764131
 2048       1000             0.00               44.89                2.739982
 4096       1000             0.00               84.23                2.570454
 8192       1000             0.00               97.31                1.484812
 16384      1000             0.00               98.08                0.748279
 32768      1000             0.00               98.12                0.374281
 65536      1000             0.00               98.14                0.187187
 131072     1000             0.00               96.49                0.092019
 262144     1000             0.00               97.29                0.046393
 524288     1000             0.00               97.72                0.023299
 1048576    1000             0.00               97.93                0.011674
 2097152    1000             0.00               98.03                0.005843
 4194304    1000             0.00               98.08                0.002923
 8388608    1000             0.00               98.11                0.001462
---------------------------------------------------------------------------------------
=======================================================================================
[root@localhost rdma]#
"""


def get_output_categories(ib_bw_output):
    category_info = {'dev_line': None, 'qp_num_line': None, 'conn_type_line': None, 'srq_line': None, 
                     'rx_depth_line': None, 'mtu_line': None, 'rdma_cm_qps_line': None, 'data_method_line': None, 
                     'local_qpn_line_list': [], 'remote_qpn_line_list': [], 'bw_line_list': []}
    output_list = ib_bw_output.splitlines()
    for i, line in enumerate(output_list):
        if 'Device' in line:
            category_info['dev_line'] = line
        if 'Number of qps' in line:
            category_info['qp_num_line'] = line
        if 'Connection type' in line:
            category_info['conn_type_line'] = line
        if 'Using SRQ' in line:
            category_info['srq_line'] = line
        if 'RX depth' in line:
            category_info['rx_depth_line'] = line
        if 'Mtu' in line:
            category_info['mtu_line'] = line
        if 'rdma_cm QPs' in line:
            category_info['rdma_cm_qps_line'] = line
        if 'Data ex. method' in line:
            category_info['data_method_line'] = line
        if 'local address' in line:
            category_info['local_qpn_line_list'].append(line)
        if 'remote address' in line:
            category_info['remote_qpn_line_list'].append(line)
        if 'bytes' in line:
            category_info['bw_line_list'] = [l for l in output_list[i + 1:] if l.strip() and '----' not in l]
    return category_info


def get_dev(dev_line):
    if match := re.search(r".*Device\s*:\s*(\S+)", dev_line):
        return match.group(1).strip()


def get_qp_num(qp_num_line):
    if match := re.search(r"Number of qps\s*:\s*(\d+)", qp_num_line):
        return int(match.group(1))
    

def get_connection_type(connection_type_line):
    if match := re.search(r"Connection type\s*:\s*(\S+)", connection_type_line):
        return match.group(1)
    

def get_srq_status(srq_status_line):
    if match := re.search(r"Using SRQ\s*:\s*(.+)", srq_status_line):
        return match.group(1).strip()
    

def get_rx_depth(rx_depth_line):
    if match := re.search(r"RX depth\s*:\s*(\d+)", rx_depth_line):
        return int(match.group(1))
    

def get_mtu(mtu_line):
    if match := re.search(r"Mtu\s*:\s*(\d+)\[B\]", mtu_line):
        return int(match.group(1))
    

def get_rdma_cm_qps_status(rdma_cm_qps_status_line):
    if match := re.search(r"rdma_cm QPs\s*:\s*(\S+)", rdma_cm_qps_status_line):
        return match.group(1)


def get_data_method(data_method_line):
    if match := re.search(r"Data ex. method\s*:\s*(\S+)", data_method_line):
        return match.group(1)


def get_local_qpn_list(local_qpn_line_list):
    local_qpn_list = list()
    for line in local_qpn_line_list:
        if match := re.search(r"local address:.*QPN\s+(0x[0-9a-fA-F]+)", line):
            local_qpn_list.append(match.group(1))
    return local_qpn_list


def get_remote_qpn_list(remote_qpn_line_list):
    remote_qpn_list = list()
    for line in remote_qpn_line_list:
        if match := re.search(r"remote address:.*QPN\s+(0x[0-9a-fA-F]+)", line):
            remote_qpn_list.append(match.group(1))
    return remote_qpn_list


def get_bw_result(bw_result_line_list):
    bw_res = {}
    for line in bw_result_line_list:
        if match := re.search(r"(\d+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", line):
            msg_size = int(match.group(1))
            bw_res[msg_size] = {'iterations': int(match.group(2)), 'bw_peak': float(match.group(3)), 
                                'bw_avg': float(match.group(4)), 'msgrate': float(match.group(5))}
    return bw_res


def get_perftest_result(perftest_output: str) -> dict:
    """解析 ib_send_bw 输出并返回结果字典"""
    cate_info = get_output_categories(perftest_output)
    perftest_res = {
        'device': get_dev(cate_info.get('dev_line')),
        'qp_num': get_qp_num(cate_info.get('qp_num_line')),
        'conn_type': get_connection_type(cate_info.get('conn_type_line')),
        'srq': get_srq_status(cate_info.get('srq_line')),
        'rx_depth': get_rx_depth(cate_info.get('rx_depth_line')),
        'mtu': get_mtu(cate_info.get('mtu_line')),
        'rdma_cm_qps': get_rdma_cm_qps_status(cate_info.get('rdma_cm_qps_line')),
        'data_method': get_data_method(cate_info.get('data_method_line')),
        'local_qpn_list': get_local_qpn_list(cate_info.get('local_qpn_line_list')),
        'remote_qpn_list': get_remote_qpn_list(cate_info.get('remote_qpn_line_list')),
        'bw_result': get_bw_result(cate_info.get('bw_line_list'))
    }
    return perftest_res


perf_res = get_perftest_result(output)
from pprint import pprint
pprint(perf_res)
