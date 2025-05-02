import threading
import traceback
from queue import Queue, Empty
import time
import paramiko
from robot.api import logger
import os
from datetime import datetime

class Consts:
    SPLIT_LINE = '--' * 50

class SSH2Connection:
    def __init__(self, ip, username, password, port='22', timeout=600):
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
        try:
            self.ssh_conn.close()
            logger.info(f"SSH connection to {self.ip} closed.", also_console=True)
        except Exception as e:
            logger.error(f"Error closing SSH connection: {e}")
      
    def execute(self, cmd, live_print: bool=False, timeout: float=None):
        try:
            _, stdout, stderr = self.ssh_conn.exec_command(cmd, timeout=timeout, get_pty=True)
            output_buffer = []
            if live_print:
                while not stdout.channel.exit_status_ready():
                    if stdout.channel.recv_ready():
                        output_line = stdout.readline()
                        output_buffer.append(output_line)
                        logger.info(output_line, also_console=True)
                remain_output = stdout.read().decode()
                output_buffer.append(remain_output)
                logger.info(remain_output, also_console=True)
            else:
                cmd_stdout = stdout.read().decode('utf-8')
                logger.info(cmd_stdout, also_console=True)
                output_buffer.append(cmd_stdout)
            cmd_stderr = stderr.read().decode('utf-8')
            if cmd_stderr:
                logger.error(f'Error: {cmd_stderr}')
                output_buffer.append(cmd_stderr)
            return ''.join(output_buffer)
        except Exception as e:
            logger.error(f"Error executing command '{cmd}': {e}\n{traceback.format_exc()}")
            return f"Exception occurred during execute: {e}"
        

class Host:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.device = SSH2Connection(ip=self.ip, username=self.username, password=self.password)

    def send_ctrl_c_to_process(self, pid):
        logger.info(f'Send CTRL+C to the process with PID: {pid}', also_console=True)
        self.device.execute(f'kill -SIGINT {pid}')
    
    def get_cmd_pid(self, cmd):
        logger.info(f'Get the process ID of command: \n{cmd}', also_console=True)
        pid_output = self.device.execute(f'pgrep -f "{cmd}"')
        try:
            cmd_pid = int(pid_output.strip())
            logger.info(f"PID of cmd:\n{cmd}\n is: {cmd_pid}", also_console=True)
            return cmd_pid
        except Exception as e:
            logger.error(f"Failed to get the process ID of command: {cmd}")
            logger.info(f'Error info:\n{str(e)}', also_console=True)
            traceback.print_exc()
            return None


class CommandThread(threading.Thread):
    def __init__(self, host_dev: Host, command: str, output_file_path: str=None, live_print: bool=False):
        super().__init__()
        self.host_dev = host_dev
        self.command = command
        self.stop_event = threading.Event()
        self.output_queue = Queue()
        self._output = None
        # self.max_queue_size_bytes = 10 * 1024 * 1024  # 10MB
        self.buffered_output = []
        self.total_bytes = 0
        self.output_file = output_file_path
        self.live_print = live_print
        logger.info(Consts.SPLIT_LINE, also_console=True)
        logger.info(f'Save output file path: {self.output_file}', also_console=True)

    def run(self):
        try:
            logger.info(Consts.SPLIT_LINE, also_console=True)
            logger.info(f"Starting command in thread: {self.command}", also_console=True)

            # 使用可持续读取的方式替代 blocking read
            _, stdout, stderr = self.host_dev.device.ssh_conn.exec_command(self.command, get_pty=True)
            stdout_channel = stdout.channel

            while not stdout_channel.exit_status_ready():
                if stdout_channel.recv_ready():
                    line = stdout_channel.recv(1024).decode('utf-8')
                    if self.live_print:
                        logger.info(line, also_console=True)
                    self._buffer_output(line)

            # 最后的残留数据
            final_out = stdout.read().decode('utf-8')
            self._buffer_output(final_out)
            cmd_err = stderr.read().decode('utf-8')
            if cmd_err:
                logger.error(f'Error: {cmd_err}')
                self._buffer_output(cmd_err)

        except Exception as e:
            error_msg = f"Thread error: {e}\n{traceback.format_exc()}"
            logger.error(error_msg)
            self.output_queue.put(error_msg)
        finally:
            self._flush_to_file()  # flush any remaining output
            if self.stop_event.is_set():
                logger.info("Thread stopped by stop_event.", also_console=True)

    def _buffer_output(self, text):
        if not text:
            return
        self.buffered_output.append(text)
        self.total_bytes += len(text.encode('utf-8'))

        if self.output_file:
            self._flush_to_file()
        else:
            self._flush_to_queue()

    def _flush_to_file(self):
        if self.buffered_output:
            joined_output = ''.join(self.buffered_output)
            with open(self.output_file, 'a') as fp:
                fp.write(joined_output)
                fp.flush()
                self.buffered_output.clear()
                self.total_bytes = 0

    def _flush_to_queue(self):
        if self.buffered_output:
            self.output_queue.put(''.join(self.buffered_output))
            self.buffered_output.clear()
            self.total_bytes = 0

    def stop(self, timeout=5):
        logger.info(Consts.SPLIT_LINE, also_console=True)
        logger.info("Stopping command thread...", also_console=True)
        self.stop_event.set()
        pid = self.host_dev.get_cmd_pid(self.command)
        if pid:
            self.host_dev.send_ctrl_c_to_process(pid)
            time.sleep(0.5)
        try:
            self.host_dev.device.disconnect()
        except Exception as e:
            logger.warn(f"Error during disconnect: {e}")
        self.join(timeout=timeout)
        if self.is_alive():
            logger.warn("Thread did not stop cleanly within timeout.")
        else:
            logger.info("Command thread stopped.", also_console=True)

    def get_output(self, timeout=None):
        self.join(timeout=timeout)
        if self.is_alive():
            logger.warn("Thread is still running; output may be incomplete.")
        
        if self.output_file:
            try:
                with open(self.output_file, 'r') as f:
                    return ''.join(f.readlines())
            except Exception as e:
                logger.error(f"Failed to read output file: {e}")
                return ""
        else:
            # 获取队列中所有输出，拼接返回
            outputs = []
            while True:
                try:
                    out = self.output_queue.get_nowait()
                    outputs.append(out)
                except Empty:
                    break
            return ''.join(outputs)


if __name__ == "__main__":
    host_ip, host_username, host_passwd = '192.168.64.101', 'root', 'a'
    ht = Host(host_ip, host_username, host_passwd)
    cmd = 'ping 127.0.0.1'
    # cmd = 'ping 12'

    # th = CommandThread(ht, cmd, output_file_path='test_output_01.txt', live_print=True)
    th = CommandThread(ht, cmd, live_print=True)
    th.start()

    time.sleep(10)

    th.stop()

    output = th.get_output(timeout=5)
    logger.info(Consts.SPLIT_LINE, also_console=True)
    logger.info(f"Final output: \n\n{output}", also_console=True)
    logger.info(Consts.SPLIT_LINE, also_console=True)
