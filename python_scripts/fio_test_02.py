import os
import time
import json
from typing import List, Tuple
import paramiko
from robot.api import logger


time_str = time.strftime("%Y%m%d_%H%M%S", time.localtime())

class Consts:
    SPLIT_LINE = '--' * 50

class SSH2Connection:
    def __init__(self, ip: str, username: str, password: str, port: str='22', timeout: int=600) -> None:
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

    def execute(self, cmd: str, timeout: int=None):
        _, stdout, stderr = self.ssh_conn.exec_command(cmd, timeout=timeout)
        cmd_stdout = stdout.read().decode('utf-8').strip()
        cmd_stderr = stderr.read().decode('utf-8').strip()
        output = cmd_stdout + "\n" + cmd_stderr if cmd_stderr else cmd_stdout
        return output


class Host:
    def __init__(self, ip: str, username: str, password: str) -> None:
        self.ip = ip
        self.username = username
        self.password = password
        self.device = SSH2Connection(ip=self.ip, username=self.username, password=self.password)
        self.log_base_dir = '/home/test_log/'
        self.log_dir_path = os.path.join(self.log_base_dir, time_str)
        self.device.execute(f'mkdir -p {self.log_dir_path}')

    def fio_test(self, fio_test_dev_list: List[str], rw_list: List[str], bs_list: List[str], iodepth_list: List[int], 
                 numjobs_list: List[int], run_time: int, fio_path: str=None, env_list: List[str]=None, 
                 test_name: str='fio_test', ioengine: str='libaio', direct: bool=True, thread: int=1, size: str='1G', 
                 ramp_time: str='5s', iodepth_batch: int=16, iodepth_batch_complete: int=32):

        logger.info(Consts.SPLIT_LINE, also_console=True)
        logger.info(f"Start fio test on host {self.ip}", also_console=True)
        logger.info(f"Test devices: {fio_test_dev_list}", also_console=True)
        res_list = list()
        for rw in rw_list:
            for bs in bs_list:
                for iodepth in iodepth_list:
                    for numjobs in numjobs_list:
                        fio_res = self.exec_fio_test(env_list, fio_path, test_name, ioengine, fio_test_dev_list, rw, bs,
                                                     iodepth, numjobs, run_time, direct=direct, thread=thread, 
                                                     size=size, ramp_time=ramp_time, iodepth_batch=iodepth_batch, 
                                                     iodepth_batch_complete=iodepth_batch_complete)
                        res_list.append(fio_res)
        self.display_fio_result(res_list)
        logger.info(f"Fio test completed on host {self.ip}", also_console=True)
        logger.info(Consts.SPLIT_LINE, also_console=True)

    def exec_fio_test(self, env_list: List[str], fio_path: str, test_name: str, ioengine: str, 
                      fio_test_dev_list: List[str], rw: str, bs: str, iodepth: int, numjobs: int, run_time: int, 
                      direct: int=1, thread: int=1, size: str='1G', ramp_time: str='5s', iodepth_batch: int=16, 
                      iodepth_batch_complete: int=32):
        logger.info(f"Running fio with rw={rw}, bs={bs}, iodepth={iodepth}, numjobs={numjobs}", 
                    also_console=True)

        fio_cmd, output_file = self.get_fio_cmd(
            test_file_list=fio_test_dev_list,
            rw_type=rw,
            bs=bs,
            iodepth=iodepth,
            numjobs=numjobs,
            run_time=run_time,
            fio_path=fio_path,
            env_list=env_list,
            test_name=test_name,
            ioengine=ioengine,
            direct=direct,
            thread=thread,
            size=size,
            ramp_time=ramp_time,
            iodepth_batch=iodepth_batch,
            iodepth_batch_complete=iodepth_batch_complete
        )

        logger.info(f"Executing fio command: \n{fio_cmd}", also_console=True)
        fio_output = self.device.execute(fio_cmd, timeout=run_time + 60)
        logger.info(Consts.SPLIT_LINE, also_console=True)
        logger.info(f'output of fio test for rw: {rw}, bs: {bs}, iodepth: {iodepth}, numjobs: '
                    f'{numjobs}:\n{fio_output}', also_console=True)
        fio_ouput_file_content = self.device.execute(f'cat {output_file}')
        fio_res = self.get_fio_result(fio_ouput_file_content)
        fio_res.update({'rw': rw, 'bs': bs, 'iodepth': iodepth, 'numjobs': numjobs})
        logger.info(Consts.SPLIT_LINE, also_console=True)
        logger.info(f'Result of fio test for rw: {rw}, bs: {bs}, iodepth: {iodepth}, numjobs: '
                    f'{numjobs}:\n{fio_res}', also_console=True)
        logger.info(Consts.SPLIT_LINE, also_console=True)
        return fio_res

    @staticmethod
    def get_fio_result(fio_json_file_content: str) -> dict:
        """
        解析fio JSON格式输出内容，提取read/write的bw（MiB/s）、iops（io/s）和latency（us）。
        返回结构示例：
        {
            'bw_unit': 'MiB/sec',
            'iops_unit': 'io/s',
            'latency_unit': 'us',
            'read': {
                'bw': 123.45,
                'iops': 1234.56,
                'latency': {'avg': 123.0, 'min': 100.0, 'max': 150.0}
            },
            'write': {
                'bw': 654.32,
                'iops': 4321.0,
                'latency': {'avg': 230.0, 'min': 200.0, 'max': 280.0}
            }
        }
        """
        try:
            data = json.loads(fio_json_file_content)
        except json.JSONDecodeError:
            logger.error("Failed to parse FIO JSON content.")
            return {}

        result = {
            'bw_unit': 'MiB/sec',
            'iops_unit': 'io/s',
            'latency_unit': 'us',
            'read': {'bw': 0.0, 'iops': 0.0, 'latency': {'avg': 0.0, 'min': 0.0, 'max': 0.0}},
            'write': {'bw': 0.0, 'iops': 0.0, 'latency': {'avg': 0.0, 'min': 0.0, 'max': 0.0}}
        }

        jobs = data.get('jobs', [])
        if not jobs:
            logger.error("No jobs found in FIO result.")
            return result

        job_count = 0
        for job in jobs:
            for mode in ['read', 'write']:
                if mode in job and job[mode].get('io_bytes', 0) > 0:
                    io_data = job[mode]
                    lat_ns = io_data.get('lat_ns', {})
                    result[mode]['bw'] += io_data.get('bw', 0.0) / 1024  # KB/s -> MiB/s
                    result[mode]['iops'] += io_data.get('iops', 0.0)
                    result[mode]['latency']['avg'] += lat_ns.get('mean', 0.0) / 1000  # ns -> us
                    result[mode]['latency']['min'] += lat_ns.get('min', 0.0) / 1000
                    result[mode]['latency']['max'] += lat_ns.get('max', 0.0) / 1000
            job_count += 1

        if job_count > 0:
            for mode in ['read', 'write']:
                for key in ['avg', 'min', 'max']:
                    result[mode]['latency'][key] = round(result[mode]['latency'][key], 2)
                result[mode]['bw'] = round(result[mode]['bw'], 2)
                result[mode]['iops'] = round(result[mode]['iops'], 2)

        return result

    def get_fio_cmd(self, test_file_list: List[str], rw_type: str, bs: str, iodepth: int, numjobs: int, run_time: int, 
                    fio_path: str=None, env_list: List[str]=None, test_name: str='fio_test', ioengine: str='libaio', 
                    direct: bool=True, thread: int=1, size: str='1G', ramp_time: str='5s', iodepth_batch: int=16, 
                    iodepth_batch_complete: int=32) -> Tuple[str, str]:
        cmd_parts = env_list if env_list else []
        fio_path = fio_path if fio_path else 'fio'
        test_file_str = ':'.join(test_file_list)
        time_str = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        output_filename = f'{test_name}_rw_{rw_type}_bs_{bs}_iodepth_{iodepth}_numjobs_{numjobs}_{time_str}.json'
        output_file = f'{self.log_dir_path}/{output_filename}'
        cmd_parts.extend([fio_path, f'-name={test_name}', f'-ioengine={ioengine}', f'-filename={test_file_str}', 
                          f'-rw={rw_type}', f'-bs={bs}', f'-iodepth={iodepth}', f'-numjobs={numjobs}', 
                          f'-runtime={run_time}', '-time_based', f'-size={size}', f'-direct={1 if direct else 0}', 
                          f'-thread={thread}', f'-ramp_time={ramp_time}', '-group_reporting -norandommap', 
                          f'-iodepth_batch={iodepth_batch}', f'-iodepth_batch_complete={iodepth_batch_complete}', 
                          '-output-format=json', f'-output={output_file}'])
        return ' '.join(cmd_parts), output_file

    # def display_fio_result(self, fio_result_list: List[dict]):
    #     """
    #     display the result of fio test for all parameters as the following form:
    #     +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #     RW    BS    IODEPTH    NUMJOBS    READ BW(Mib/sec)    READ IOPS(io/s)    READ AVG LAT(us)    WRITE BW(Mib/sec)    WRITE IOPS(io/s)    WRITE AVG LAT(us)
    #     -------------------------------------------------------------------------------------------------------------------------------------------------------
    #     ....
    #     ....
    #     ....
    #     +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    #     """
    def display_fio_result(self, fio_result_list: List[dict]):
        if not fio_result_list:
            logger.warn("No FIO result to display.", also_console=True)
            return

        headers = [
            "RW", "BS", "IODEPTH", "NUMJOBS",
            "READ BW(MiB/sec)", "READ IOPS(io/s)", "READ AVG LAT(us)",
            "WRITE BW(MiB/sec)", "WRITE IOPS(io/s)", "WRITE AVG LAT(us)"
        ]

        # 打印标题分隔线
        table_width = 152
        sep_line = "+" + "-" * (table_width - 2) + "+"
        logger.info(sep_line, also_console=True)
        logger.info("{:<8}{:<8}{:<10}{:<10}{:<20}{:<20}{:<20}{:<20}{:<20}{:<20}".format(*headers), also_console=True)
        logger.info("-" * table_width, also_console=True)

        # 打印每组结果
        for res in fio_result_list:
            rw = res.get('rw', '')
            bs = res.get('bs', '')
            iodepth = res.get('iodepth', '')
            numjobs = res.get('numjobs', '')

            read = res.get('read', {})
            write = res.get('write', {})

            read_bw = read.get('bw', 0.0)
            read_iops = read.get('iops', 0.0)
            read_lat = read.get('latency', {}).get('avg', 0.0)

            write_bw = write.get('bw', 0.0)
            write_iops = write.get('iops', 0.0)
            write_lat = write.get('latency', {}).get('avg', 0.0)

            logger.info("{:<8}{:<8}{:<10}{:<10}{:<20}{:<20}{:<20}{:<20}{:<20}{:<20}".format(
                rw, bs, str(iodepth), str(numjobs),
                f"{read_bw:.2f}", f"{read_iops:.2f}", f"{read_lat:.2f}",
                f"{write_bw:.2f}", f"{write_iops:.2f}", f"{write_lat:.2f}"
            ), also_console=True)

        logger.info(sep_line, also_console=True)



if __name__ == "__main__":
    host_ip, host_username, host_passwd = '192.168.64.101', 'root', 'a'
    ht = Host(host_ip, host_username, host_passwd)
    ht.fio_test(['/dev/nullb0'], ['read', 'write', 'rw'], ['4k', '1m'], [64, 1024], [1, 4], 30)

