#!/usr/bin/env python3

import asyncio
import argparse
import os
import sys
import subprocess
from tapo import ApiClient
from datetime import datetime

HOSTS_DELIMITER = "### LAPTOP-BRICK ###"
BLOCKLIST_FILE_PATH = "blocklist"
HOSTS_FILE_PATH = (
    r"C:\Windows\System32\drivers\etc\hosts" if os.name == "nt" else "/etc/hosts"
)

def _flush_dns_cache():
    try:
        if os.name == 'nt':
            subprocess.run(["ipconfig", "/flushdns"], check=True)
        else:
            subprocess.run(["sudo", "dscacheutil", "-flushcache"], check=True)
            subprocess.run(["sudo", "killall", "-HUP", "mDNSResponder"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error blocking sites: {e}", file=sys.stderr)


def _read_blocklist() -> list[str]:
    with open(BLOCKLIST_FILE_PATH, "r") as f:
        lines = f.readlines()
   
    lines = [line.strip() for line in lines]
    return lines


def _update_hosts_file(should_block: bool, blocklist: list[str]):
    try:
        with open(HOSTS_FILE_PATH, "r") as f:
            # Write contents of hostfile unrelated to blocklist
            lines = f.readlines()
            new_lines = []
            for line in lines:
                if line == HOSTS_DELIMITER or HOSTS_DELIMITER in line:
                    break
                new_lines.append(line.rstrip())
        
        with open(HOSTS_FILE_PATH, 'w') as f:
            # Block URLs in blocklist if needed     
            if should_block:
                print(f"Blocking {len(blocklist)} sites...")
                new_lines.extend([HOSTS_DELIMITER] + blocklist + [HOSTS_DELIMITER])
                            
            # Update hosts file and flush DNS cache to make hosts changes take effect
            f.write('\n'.join(new_lines))
            _flush_dns_cache()

    except Exception as e:
        print(f"Error reading hosts file: {e}", file=sys.stderr)


async def monitor_plug(ip_address, username, password):
    client = ApiClient(username, password)
    device = await client.p110(ip_address)
    print(f"Connected to device at {ip_address}")
    print("Monitoring device state. Press Ctrl+C to exit.")
    
    # Read blocklist 
    blocklist = _read_blocklist()
    print("Will block these URLs when plug is on: " + '\n'.join(blocklist) + "\n")
    
    # Initial state
    device_info = await device.get_device_info()
    last_state = device_info.device_on
    print(f"Initial state: {'ON' if last_state else 'OFF'}")
    _update_hosts_file(last_state, blocklist)
    
    # Continuously monitor
    while True:
        device_info = await device.get_device_info()
        current_state = device_info.device_on
        
        # Only print and update hosts when state changes
        if current_state != last_state:
            print(f"Device is now: {'ON' if current_state else 'OFF'}")
            _update_hosts_file(current_state, blocklist)
            last_state = current_state
       
        # Wait before polling again 
        await asyncio.sleep(1)

def is_admin():
    if os.name == 'nt':  # Windows
        # Check write permission to hosts file as a proxy for admin
        return os.access(HOSTS_FILE_PATH, os.W_OK)
    else:  # Unix/macOS
        return os.geteuid() == 0


def main():
    if not is_admin():
        print("Warning: This script needs root privileges to modify /etc/hosts", file=sys.stderr)
        print("Please run with sudo", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Monitor TP Link Tapo Plug state and manage hosts file")
    parser.add_argument("--ip_address", help="IP address of the Tapo plug")
    parser.add_argument("--username", help="Tapo account username")
    parser.add_argument("--password", help="Tapo account password")
    args = parser.parse_args()

    # Run the async monitoring function
    asyncio.run(monitor_plug(args.ip_address, args.username, args.password))
 
if __name__ == "__main__":
    main()