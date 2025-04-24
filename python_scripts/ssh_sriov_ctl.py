import os
import argparse
import subprocess
import paramiko

SPLIT_LINE = "-" * 110

def remote_execute(ssh_client, command):
    stdin, stdout, stderr = ssh_client.exec_command(command)
    output = stdout.read().decode()
    error = stderr.read().decode()
    if error:
        print(f"Error executing command: {command}\n{error}")
    return output.strip()

def enable_sriov(ssh_client, device, vf_num):
    print(SPLIT_LINE)
    print(f"Enabling SR-IOV for device: {device}")

    command = f"cat /sys/bus/pci/devices/{device}/sriov_totalvfs"
    max_vfs_output = remote_execute(ssh_client, command)
    try:
        max_vfs = int(max_vfs_output)
    except ValueError:
        print(f"Device {device} does not support SR-IOV or error fetching max_vfs")
        return

    if vf_num is None or vf_num > max_vfs:
        vf_num = max_vfs

    command = f"echo {vf_num} > /sys/bus/pci/devices/{device}/sriov_numvfs"
    remote_execute(ssh_client, command)
    print(f"Enabled {vf_num} VFs for device {device}")

def disable_sriov(ssh_client, device):
    print(f"Disabling SR-IOV for device: {device}")
    command = f"echo 0 > /sys/bus/pci/devices/{device}/sriov_numvfs"
    remote_execute(ssh_client, command)
    print(f"Disabled SR-IOV for device {device}")

def init_devices(ssh_client, net_device, rdma_device):
    if not net_device:
        command = "lspci -D | grep -i 'red' | awk '{print $1}'"
        net_devices = remote_execute(ssh_client, command).splitlines()
    else:
        net_devices = [net_device]

    if not rdma_device:
        command = "lspci -D | grep -i 'xi' | awk '{print $1}'"
        rdma_devices = remote_execute(ssh_client, command).splitlines()
    else:
        rdma_devices = [rdma_device]

    return net_devices, rdma_devices

def show_pcie_devs(ssh_client):
    command = "lspci -D | grep -E -i 'red|xi'"
    print(remote_execute(ssh_client, command))

def sriov_control(ssh_client, devices, action, vf_cnt):
    for dev in devices:
        if action == "enable":
            enable_sriov(ssh_client, dev, vf_cnt)
        elif action == "disable":
            disable_sriov(ssh_client, dev)
        else:
            print("Invalid action. Please use 'enable' or 'disable'.")
            exit(1)

def main():
    parser = argparse.ArgumentParser(description="SR-IOV management script via SSH")
    parser.add_argument("-a", "--action", required=True, choices=["enable", "disable"], help="SRIOV action (enable/disable)")
    parser.add_argument("-n", "--net_device", help="Net function ID")
    parser.add_argument("-r", "--rdma_device", help="RDMA function ID")
    parser.add_argument("-c", "--vf_count", type=int, help="Number of VFs to enable")
    parser.add_argument("--host", required=True, help="Remote host address")
    parser.add_argument("--user", required=True, help="SSH username")
    parser.add_argument("--password", required=True, help="SSH password")
    args = parser.parse_args()

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(args.host, username=args.user, password=args.password)
        print(f"Connected to {args.host}")

        net_devices, rdma_devices = init_devices(ssh_client, args.net_device, args.rdma_device)

        print(SPLIT_LINE)
        print("PCIe devices before setting SR-IOV:")
        show_pcie_devs(ssh_client)
        print(SPLIT_LINE)

        if args.action == "enable":
            sriov_control(ssh_client, rdma_devices, args.action, args.vf_count)
            sriov_control(ssh_client, net_devices, args.action, args.vf_count)
        elif args.action == "disable":
            sriov_control(ssh_client, net_devices, args.action, args.vf_count)
            sriov_control(ssh_client, rdma_devices, args.action, args.vf_count)

        print(SPLIT_LINE)
        print("PCIe devices after setting SR-IOV:")
        show_pcie_devs(ssh_client)
        print(SPLIT_LINE)

    finally:
        ssh_client.close()
        print(f"Disconnected from {args.host}")

if __name__ == "__main__":
    main()
