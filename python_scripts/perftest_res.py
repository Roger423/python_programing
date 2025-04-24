import re
from pprint import pprint

# 测试结果字符串
test_output = """
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
"""

# 初始化结果字典
res = {
    'device': '',
    'qp_num': 0,
    'conn_type': '',
    'srq': '',
    'rx_depth': 0,
    'mtu': 0,
    'rdma_cm_qps': '',
    'data_method': '',
    'local_qpn_list': [],
    'remote_qpn_list': [],
    'bw_result': {}
}

# 改进提取测试信息的正则表达式
test_info_pattern = re.compile(r"([\w\s]+?)\s*:\s*([^:]+)")
for match in test_info_pattern.finditer(test_output):
    key = match.group(1).strip().replace(" ", "_").replace("(", "").replace(")", "")
    value = match.group(2).strip()

    if key == 'Device':
        res['device'] = value
    elif key == 'Number_of_qps':
        res['qp_num'] = int(value)
    elif key == 'Connection_type':
        res['conn_type'] = value
    elif key == 'Using_SRQ':
        res['srq'] = value
    elif key == 'RX_depth':
        res['rx_depth'] = int(value)
    elif key == 'Mtu':
        res['mtu'] = int(value.replace('[B]', ''))
    elif key == 'rdma_cm_QPs':
        res['rdma_cm_qps'] = value
    elif key == 'Data_ex._method':
        res['data_method'] = value

# 打印提取的字段以进行调试
print("提取的字段:")
for key, value in res.items():
    print(f"{key}: {value}")

# 提取本地和远程 QPN
local_qpn_pattern = re.compile(r"local address:.*QPN\s+(0x[0-9a-f]+)")
remote_qpn_pattern = re.compile(r"remote address:.*QPN\s+(0x[0-9a-f]+)")

local_qpn_match = local_qpn_pattern.search(test_output)
remote_qpn_match = remote_qpn_pattern.search(test_output)

if local_qpn_match:
    res['local_qpn_list'].append(local_qpn_match.group(1))
if remote_qpn_match:
    res['remote_qpn_list'].append(remote_qpn_match.group(1))

# 提取结果数据
results_pattern = re.compile(r"(\d+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)")
for match in results_pattern.finditer(test_output):
    msg_size = int(match.group(1))
    iterations = int(match.group(2))
    bw_peak = float(match.group(3))
    bw_average = float(match.group(4))
    msg_rate = float(match.group(5))

    res['bw_result'][msg_size] = {
        'iterations': iterations,
        'bw_peak': bw_peak,
        'bw_avg': bw_average,
        'msgrate': msg_rate
    }

# 打印结果字典
pprint(res)
