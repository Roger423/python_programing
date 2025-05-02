import threading
import traceback
from queue import Queue
import time
import paramiko
from robot.api import logger


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

    def execute(self, cmd, timeout=None):
        try:
            _, stdout, stderr = self.ssh_conn.exec_command(cmd, timeout=timeout)
            cmd_stdout = stdout.read().decode('utf-8').strip()
            cmd_stderr = stderr.read().decode('utf-8').strip()
            output = cmd_stdout + "\n" + cmd_stderr if cmd_stderr else cmd_stdout
            return output
        except Exception as e:
            logger.error(f"Error executing command '{cmd}': {e}")
            return ""


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
    def __init__(self, host_dev: Host, command: str):
        super().__init__()
        self.host_dev = host_dev
        self.command = command
        self.stop_event = threading.Event()
        self.output_queue = Queue()
        self._output = None

    def run(self):
        try:
            logger.info(f"Starting command in thread: {self.command}", also_console=True)
            # Execute command with a timeout to prevent hanging
            output = self.host_dev.device.execute(self.command, timeout=60)  # 60-second timeout
            self._output = output
            self.output_queue.put(output)
            logger.info(f"Command output: {output}", also_console=True)
        except Exception as e:
            error_msg = f"Thread error: {e}\n{traceback.format_exc()}"
            logger.error(error_msg)
            self.output_queue.put(error_msg)
        finally:
            if self.stop_event.is_set():
                logger.info("Thread stopped by stop_event.", also_console=True)

    def stop(self, timeout=5):
        logger.info("Stopping command thread...", also_console=True)
        self.stop_event.set()

        # Attempt to terminate the remote process
        pid = self.host_dev.get_cmd_pid(self.command)
        if pid:
            self.host_dev.send_ctrl_c_to_process(pid)
            # Give the process a moment to terminate
            time.sleep(0.5)

        # Close the SSH connection to unblock exec_command
        try:
            self.host_dev.device.disconnect()
        except Exception as e:
            logger.warn(f"Error during disconnect: {e}")

        # Wait for the thread to terminate
        self.join(timeout=timeout)
        if self.is_alive():
            logger.warn("Thread did not stop cleanly within timeout.")
        else:
            logger.info("Command thread stopped.", also_console=True)

    def get_output(self, block=True, timeout=None):
        try:
            return self.output_queue.get(block=block, timeout=timeout)
        except Queue.Empty:
            logger.warn("Output not ready or thread was stopped prematurely.")
            return self._output if self._output is not None else ""

if __name__ == "__main__":
    # Example usage
    host_ip, host_username, host_passwd = '192.168.64.101', 'root', 'a'
    ht = Host(host_ip, host_username, host_passwd)
    cmd = 'ping 127.0.0.1'

    # Create and start the command thread
    th = CommandThread(ht, cmd)
    th.start()

    # Let it run for 10 seconds
    time.sleep(10)

    # Stop the thread and terminate the remote process
    th.stop()

    # Retrieve and log the output
    output = th.get_output(block=True, timeout=5)
    logger.info(f"Final output: {output}", also_console=True)
