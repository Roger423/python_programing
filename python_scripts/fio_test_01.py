import os
import time
import json
from typing import List, Tuple, Optional, Dict
import paramiko
from robot.api import logger
import shlex
import configparser
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global time string for log directory
time_str = time.strftime("%Y%m%d_%H%M%S", time.localtime())

class Consts:
    SPLIT_LINE = '--' * 50
    CONFIG_FILE = "config.ini"
    DEFAULT_LOG_BASE_DIR = "/tmp/test_log/"  # Changed to /tmp/ for better accessibility

class SSH2Connection:
    def __init__(self, ip: str, username: str, password: str, port: str = '22', timeout: int = 600) -> None:
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.ssh_conn = paramiko.SSHClient()

    def ssh_connection(self, max_attempts: int=3, wait_seconds: int=2) -> bool:
        logger.info(Consts.SPLIT_LINE, also_console=True)
        logger.info(f'SSH connecting to {self.ip}...', also_console=True)
        for attempt in range(1, max_attempts + 1):
            try:
                if not self.username:
                    logger.error("Username is None or empty.")
                    return False
                self.ssh_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh_conn.connect(
                    self.ip,
                    port=int(self.port),
                    username=self.username,
                    password=self.password,
                    timeout=self.timeout
                )
                logger.info(f"SSH connection to {self.ip} established.", also_console=True)
                return True
            except paramiko.AuthenticationException:
                logger.error("Authentication failed.")
            except paramiko.SSHException as ssh_exception:
                logger.error(f"SSH connection failed: {ssh_exception}")
            except Exception as e:
                logger.error(f"Unexpected error during SSH connection: {e}")
            if attempt < max_attempts:
                logger.info(f"Retrying SSH connection (attempt {attempt + 1}/{max_attempts})...")
                time.sleep(wait_seconds)
        logger.error(f"Failed to establish SSH connection after {max_attempts} attempts.")
        return False

    def disconnect(self) -> None:
        try:
            self.ssh_conn.close()
            logger.info(f"SSH connection to {self.ip} closed.", also_console=True)
        except Exception as e:
            logger.error(f"Error closing SSH connection: {e}")

    @contextmanager
    def ssh_session(self):
        try:
            if self.ssh_connection():
                yield self
            else:
                raise ConnectionError(f"Failed to establish SSH connection to {self.ip}")
        finally:
            self.disconnect()

    def execute(self, cmd: str, timeout: Optional[int]=None) -> str:
        if not cmd:
            logger.error("Empty command provided.")
            return ""
        if not self.ssh_conn.get_transport() or not self.ssh_conn.get_transport().is_active():
            logger.error("SSH connection is not active. Reconnecting...")
            if not self.ssh_connection():
                return ""
        cmd = shlex.quote(cmd)
        try:
            _, stdout, stderr = self.ssh_conn.exec_command(cmd, timeout=timeout)
            cmd_stdout = stdout.read().decode('utf-8').strip()
            cmd_stderr = stderr.read().decode('utf-8').strip()
            output = cmd_stdout + "\n" + cmd_stderr if cmd_stderr else cmd_stdout
            logger.debug(f"Command: {cmd}, Output: {output}")
            return output
        except Exception as e:
            logger.error(f"Command execution failed: {cmd}, Error: {e}")
            return ""

class Host:
    def __init__(self, ip: str, username: str, password: str, log_base_dir: str=Consts.DEFAULT_LOG_BASE_DIR) -> None:
        self.ip = ip
        self.username = username
        self.password = password
        self.log_base_dir = log_base_dir
        self.log_dir_path = os.path.join(self.log_base_dir, time_str)
        self.device = SSH2Connection(ip=self.ip, username=self.username, password=self.password)
        self.setup_successful = False
        with self.device.ssh_session():
            if self._create_log_dir() and self._validate_initial_setup():
                self.setup_successful = True

    def _create_log_dir(self) -> bool:
        create_base_dir_cmd = f'mkdir -p {self.log_base_dir}'
        create_log_dir_cmd = f'mkdir -p {self.log_dir_path}'
        result = self.device.execute(create_base_dir_cmd)
        if result:
            logger.error(f"Failed to create base log directory {self.log_base_dir}: {result}")
            return False
        result = self.device.execute(create_log_dir_cmd)
        if result:
            logger.error(f"Failed to create log directory {self.log_dir_path}: {result}")
            return False
        logger.info(f"Log directory {self.log_dir_path} created.", also_console=True)
        return True

    def _validate_initial_setup(self) -> bool:
        result = self.device.execute('which fio')
        if not result or "command not found" in result:
            logger.error("FIO binary not found on host. Please install FIO.")
            return False
        logger.info(f"FIO binary found at: {result}", also_console=True)
        return True

    def _validate_fio_params(self, fio_test_dev_list: List[str], rw_list: List[str], bs_list: List[str],
                            iodepth_list: List[int], numjobs_list: List[int], run_time: int) -> bool:
        if not self.setup_successful:
            logger.error("Initial setup failed. Cannot proceed with FIO tests.")
            return False
        if not all([fio_test_dev_list, rw_list, bs_list, iodepth_list, numjobs_list]):
            logger.error("One or more FIO parameter lists are empty.")
            return False
        if run_time <= 0:
            logger.error("Run time must be positive.")
            return False
        for dev in fio_test_dev_list:
            result = self.device.execute(f'[ -e {dev} ] && echo exists')
            if "exists" not in result:
                logger.error(f"Device {dev} does not exist on host {self.ip}.")
                return False
        return True

    def fio_test(self, fio_test_dev_list: List[str], rw_list: List[str], bs_list: List[str], iodepth_list: List[int],
                 numjobs_list: List[int], run_time: int, fio_path: Optional[str] = None, env_list: Optional[List[str]] = None,
                 test_name: str = 'fio_test', ioengine: str = 'libaio', direct: bool = True, thread: int = 1,
                 size: str = '1G', ramp_time: str = '5s', iodepth_batch: int = 16, iodepth_batch_complete: int = 32) -> None:

        with self.device.ssh_session():
            if not self._validate_fio_params(fio_test_dev_list, rw_list, bs_list, iodepth_list, numjobs_list, run_time):
                return

            logger.info(Consts.SPLIT_LINE, also_console=True)
            logger.info(f"Starting FIO test on host {self.ip}", also_console=True)
            logger.info(f"Test devices: {fio_test_dev_list}", also_console=True)

            def run_single_test(params: Tuple[str, str, int, int]) -> None:
                rw, bs, iodepth, numjobs = params
                logger.info(f"Running FIO with rw={rw}, bs={bs}, iodepth={iodepth}, numjobs={numjobs}", also_console=True)
                with self.device.ssh_session():
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
                    logger.info(f"Executing FIO command: \n{fio_cmd}", also_console=True)
                    fio_output = self.device.execute(fio_cmd, timeout=run_time + 60)
                    logger.info(Consts.SPLIT_LINE, also_console=True)
                    logger.info(f"Output of FIO test for rw: {rw}, bs: {bs}, iodepth: {iodepth}, numjobs: {numjobs}:\n{fio_output}", also_console=True)
                    fio_output_file_content = self.device.execute(f'cat {output_file}')
                    fio_res = self.get_fio_result(fio_output_file_content)
                    logger.info(Consts.SPLIT_LINE, also_console=True)
                    logger.info(f"Result of FIO test for rw: {rw}, bs: {bs}, iodepth: {iodepth}, numjobs: {numjobs}:\n{fio_res}", also_console=True)
                    self.device.execute(f'rm {output_file}')  # Clean up temporary file

            # Run tests sequentially to avoid SSH session conflicts
            test_params = [(rw, bs, iodepth, numjobs) for rw in rw_list for bs in bs_list for iodepth in iodepth_list for numjobs in numjobs_list]
            for params in test_params:
                run_single_test(params)

            logger.info(f"FIO test completed on host {self.ip}", also_console=True)
            logger.info(Consts.SPLIT_LINE, also_console=True)

    @staticmethod
    def get_fio_result(fio_json_file_content: str) -> Dict:
        result = {
            'bw_unit': 'MiB/sec',
            'iops_unit': 'io/s',
            'latency_unit': 'us',
            'read': {'bw': 0.0, 'iops': 0.0, 'latency': {'avg': 0.0, 'min': 0.0, 'max': 0.0}},
            'write': {'bw': 0.0, 'iops': 0.0, 'latency': {'avg': 0.0, 'min': 0.0, 'max': 0.0}}
        }
        try:
            data = json.loads(fio_json_file_content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse FIO JSON content: {e}")
            return result

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
                    result[mode]['latency'][key] = round(result[mode]['latency'][key] / job_count, 2)
                result[mode]['bw'] = round(result[mode]['bw'] / job_count, 2)
                result[mode]['iops'] = round(result[mode]['iops'] / job_count, 2)

        return result

    def get_fio_cmd(self, test_file_list: List[str], rw_type: str, bs: str, iodepth: int, numjobs: int, run_time: int,
                    fio_path: Optional[str] = None, env_list: Optional[List[str]] = None, test_name: str = 'fio_test',
                    ioengine: str = 'libaio', direct: bool = True, thread: int = 1, size: str = '1G',
                    ramp_time: str = '5s', iodepth_batch: int = 16, iodepth_batch_complete: int = 32) -> Tuple[str, str]:
        cmd_parts = env_list if env_list else []
        fio_path = fio_path or 'fio'
        test_file_str = ':'.join(test_file_list)
        time_str = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        output_filename = f"{test_name}_rw_{rw_type}_bs_{bs}_iodepth_{iodepth}_numjobs_{numjobs}_{time_str}.json"
        output_file = os.path.join(self.log_dir_path, output_filename)
        cmd_parts.extend([
            fio_path,
            f"--name={test_name}",
            f"--ioengine={ioengine}",
            f"--filename={test_file_str}",
            f"--rw={rw_type}",
            f"--bs={bs}",
            f"--iodepth={iodepth}",
            f"--numjobs={numjobs}",
            f"--runtime={run_time}",
            "--time_based",
            f"--size={size}",
            f"--direct={1 if direct else 0}",
            f"--thread={thread}",
            f"--ramp_time={ramp_time}",
            "--group_reporting",
            "--norandommap",
            f"--iodepth_batch={iodepth_batch}",
            f"--iodepth_batch_complete={iodepth_batch_complete}",
            "--output-format=json",
            f"--output={shlex.quote(output_file)}"
        ])
        return " ".join(cmd_parts), output_file

def load_config(config_file: str = Consts.CONFIG_FILE) -> Dict:
    config = configparser.ConfigParser()
    config.read(config_file)
    return {
        'host_ip': config.get('SSH', 'host_ip', fallback='192.168.64.101'),
        'host_username': config.get('SSH', 'username', fallback='root'),
        'host_password': config.get('SSH', 'password', fallback='a'),
        'log_base_dir': config.get('Paths', 'log_base_dir', fallback=Consts.DEFAULT_LOG_BASE_DIR)
    }

if __name__ == "__main__":
    config = load_config()
    ht = Host(
        ip=config['host_ip'],
        username=config['host_username'],
        password=config['host_password'],
        log_base_dir=config['log_base_dir']
    )
    ht.fio_test(
        fio_test_dev_list=['/tmp/testfile'],  # Changed to a test file
        rw_list=['read', 'write', 'rw'],
        bs_list=['4k'],
        iodepth_list=[64],
        numjobs_list=[1],
        run_time=30
    )
