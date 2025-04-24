import os
import argparse
import subprocess

SPLIT_LINE = "-" * 110

def usage():
    print(SPLIT_LINE)
    print("Usage: script.py -a <sriov action(enable/disable)> [-n <net function id>] [-r <rdma function id>] [-c <vf count>]")
    print(SPLIT_LINE)

def enable_sriov(device, vf_num):
    print(SPLIT_LINE)
    print(f"Enabling SR-IOV for device: {device}")
    try:
        with open(f"/sys/bus/pci/devices/{device}/sriov_totalvfs") as f:
            max_vfs = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        print(f"Device {device} does not support SR-IOV")
        return

    if vf_num is None or vf_num > max_vfs:
        vf_num = max_vfs

    try:
        with open(f"/sys/bus/pci/devices/{device}/sriov_numvfs", "w") as f:
            f.write(str(vf_num))
        print(f"Enabled {vf_num} VFs for device {device}")
    except Exception as e:
        print(f"Failed to enable SR-IOV for device {device}: {e}")

def disable_sriov(device):
    print(f"Disabling SR-IOV for device: {device}")
    try:
        with open(f"/sys/bus/pci/devices/{device}/sriov_numvfs", "w") as f:
            f.write("0")
        print(f"Disabled SR-IOV for device {device}")
    except Exception as e:
        print(f"Failed to disable SR-IOV for device {device}: {e}")

def init_devices(net_device, rdma_device):
    if not net_device:
        net_devices = subprocess.getoutput("lspci -D | grep -i 'red' | awk '{print $1}'").splitlines()
    else:
        net_devices = [net_device]

    if not rdma_device:
        rdma_devices = subprocess.getoutput("lspci -D | grep -i 'xi' | awk '{print $1}'").splitlines()
    else:
        rdma_devices = [rdma_device]

    return net_devices, rdma_devices

def show_pcie_devs():
    print(subprocess.getoutput("lspci -D | grep -E -i 'red|xi'"))

def sriov_control(devices, action, vf_cnt):
    for dev in devices:
        if action == "enable":
            enable_sriov(dev, vf_cnt)
        elif action == "disable":
            disable_sriov(dev)
        else:
            print("Invalid action. Please use 'enable' or 'disable'.")
            exit(1)

def main():
    parser = argparse.ArgumentParser(description="SR-IOV management script")
    parser.add_argument("-a", "--action", required=True, choices=["enable", "disable"], help="SRIOV action (enable/disable)")
    parser.add_argument("-n", "--net_device", help="Net function ID")
    parser.add_argument("-r", "--rdma_device", help="RDMA function ID")
    parser.add_argument("-c", "--vf_count", type=int, help="Number of VFs to enable")
    args = parser.parse_args()

    net_devices, rdma_devices = init_devices(args.net_device, args.rdma_device)

    print(SPLIT_LINE)
    print("PCIe devices before setting SR-IOV:")
    show_pcie_devs()
    print(SPLIT_LINE)

    if args.action == "enable":
        sriov_control(rdma_devices, args.action, args.vf_count)
        sriov_control(net_devices, args.action, args.vf_count)
    elif args.action == "disable":
        sriov_control(net_devices, args.action, args.vf_count)
        sriov_control(rdma_devices, args.action, args.vf_count)

    print(SPLIT_LINE)
    print("PCIe devices after setting SR-IOV:")
    show_pcie_devs()
    print(SPLIT_LINE)

if __name__ == "__main__":
    main()
