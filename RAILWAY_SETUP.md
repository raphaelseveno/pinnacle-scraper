# 🚀 Railway Deployment Guide - Project Acheron

Deploy Project Acheron to Railway.app in **5 minutes** with full English-language management via Claude Code.

---

## 📋 Prerequisites

You need these accounts/credentials (all free or low-cost):

1. **Railway.app account** (free $5 credit, then $5/month)
2. **Pinnacle (PS3838) account** - Your betting account
3. **PacketStream account** - Residential proxy provider ($10 prepaid, lasts 5-10 months)
4. **ntfy.sh topic** - No signup needed, just pick a unique name

---

## 🎯 Quick Start (5 Minutes)

### Step 1: Create Railway Account (1 minute)

1. Visit [railway.app](https://railway.app)
2. Click **"Start a New Project"**
3. Sign in with GitHub
4. Done! ✅

### Step 2: Deploy Acheron (2 minutes)

Click this button to deploy instantly:

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/acheron)

**OR** manually deploy:

1. In Railway dashboard, click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Connect your fork of this repository
4. Railway will auto-detect the `Dockerfile.railway` and begin building
5. Wait for build to complete (~3-5 minutes)

### Step 3: Add Redis Database (30 seconds)

1. In your Railway project, click **"+ New"**
2. Select **"Database" → "Redis"**
3. Railway automatically connects it to your app
4. Done! ✅

### Step 4: Configure Environment Variables (2 minutes)

In Railway dashboard, go to your **Acheron service** → **Variables** tab and add:

```bash
PINNACLE_USERNAME=your_pinnacle_username
PINNACLE_PASSWORD=your_pinnacle_password
PACKETSTREAM_API_KEY=your_packetstream_api_key
NTFY_TOPIC=acheron-alerts-YOUR_SECRET_NAME
```

**How to get these:**

#### Pinnacle Credentials
- Your existing PS3838 login username and password

#### PacketStream API Key
1. Visit [packetstream.io](https://packetstream.io)
2. Sign up for account
3. Add $10 credit (Dashboard → Billing → Add Credit)
4. Go to API section and copy your API key
5. Paste into Railway as `PACKETSTREAM_API_KEY`

#### ntfy Topic
- Pick any unique name (e.g., `acheron-bob-12345`)
- This is your private notification channel
- Install ntfy app on phone: [Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy) | [iOS](https://apps.apple.com/app/ntfy/id1625396347)
- Subscribe to your topic name in the app

**Save** the variables. Railway will auto-redeploy.

---

## ✅ Verify Deployment

### Check Logs

In Railway dashboard:
1. Go to your Acheron service
2. Click **"Deployments"** → Latest deployment
3. Click **"View Logs"**

You should see:
```
✅ All components initialized
🎯 PROJECT ACHERON STARTING
Step 1/4: Authenticating to Pinnacle...
✅ Authentication successful
✅ PROJECT ACHERON IS RUNNING
```

### Test Notification

Within 30 seconds of startup, you should receive a test notification on your phone:

> **🚀 Acheron Started**
> Project Acheron is now running and monitoring NHL odds in real-time.

---

## 🤖 Managing via Claude Code (English Commands)

Once deployed, you can manage everything by talking to Claude Code in natural language!

### Setup MCP Connection (One-Time)

Tell Claude Code your Railway app URL:

```
You: "Claude, here's my Railway deployment URL: https://acheron-production-xxxx.up.railway.app"
Claude: [Configures MCP connection automatically]
        ✅ Connected to Acheron Management Server
```

### Example Commands

```
You: "Start the scraper"
Claude: [Calls MCP tool: scraper_start()]
        ✅ Acheron scraper started successfully
        📊 Monitoring NHL odds on Pinnacle

You: "Is it working?"
Claude: [Calls MCP tool: scraper_status()]
        ✅ Running for 3 hours
        📈 Processed 2,547 odds updates
        🎯 Detected 4 arbitrage opportunities
        💚 All systems healthy

You: "Show me today's alerts"
Claude: [Calls MCP tool: view_alerts(date="today")]
        📊 Today's Arbitrage Opportunities (Feb 22):

        1. Bruins vs Maple Leafs (7:00 PM)
           Profit: 3.2% | Detected: 2:14 PM

        2. Rangers vs Devils (7:30 PM)
           Profit: 2.8% | Detected: 5:41 PM

You: "Change minimum profit to 3%"
Claude: [Calls MCP tool: update_config("notifications.thresholds.min_profit_percent", 3.0)]
        [Calls MCP tool: scraper_restart()]
        ✅ Updated minimum profit to 3%. Scraper restarted.

You: "Stop it for tonight"
Claude: [Calls MCP tool: scraper_stop()]
        ✅ Scraper stopped. Type "start" to resume.

You: "How much proxy credit left?"
Claude: [Calls MCP tool: proxy_status()]
        💰 $7.42 remaining (~4 months at current usage)
        📊 Used 258 MB so far

You: "Show me the last 20 log lines"
Claude: [Calls MCP tool: view_logs(lines=20)]
        [Recent log output...]

You: "Update to latest version"
Claude: [Calls MCP tool: deploy_update()]
        ✅ Updated from commit abc123 to def456
        ✅ Scraper restarted with new code
```

---

## 📊 Available MCP Tools

Claude Code has access to these management tools:

| Tool | Description |
|------|-------------|
| `scraper_status()` | Check if running, uptime, stats |
| `scraper_start()` | Start the scraper |
| `scraper_stop()` | Stop the scraper |
| `scraper_restart()` | Restart (e.g., after config change) |
| `view_alerts(date, limit)` | View arbitrage opportunities |
| `update_config(setting, value)` | Change configuration |
| `view_logs(lines, level)` | View recent log entries |
| `proxy_status()` | Check proxy balance |
| `redis_query(command)` | Debug Redis data |
| `deploy_update()` | Pull latest code from git |
| `system_info()` | View CPU/memory/disk usage |

---

## 💰 Cost Breakdown

| Service | Cost | Duration |
|---------|------|----------|
| Railway.app | **$5/month** | Ongoing |
| PacketStream Proxy | **$10 prepaid** | 5-10 months |
| Redis on Railway | **$0** | Included |
| ntfy Notifications | **$0** | Free forever |
| **Total First Month** | **$5** | |
| **Total Monthly (after)** | **$5-7** | |

**First month is FREE** thanks to Railway's $5 credit!

---

## 🔧 Configuration Options

Edit settings via Claude Code using `update_config()` tool:

### Common Settings

```python
# Minimum profit threshold
update_config("notifications.thresholds.min_profit_percent", 2.5)

# Minimum bet limit
update_config("notifications.thresholds.min_bet_limit", 1000)

# Add more leagues
update_config("sports.leagues", ["NHL", "KHL"])

# Change log level
update_config("monitoring.logging.level", "DEBUG")
```

All settings are in `config.railway.yaml` but Claude Code manages them for you!

---

## 🚨 Troubleshooting

### "Authentication Failed"

**Cause:** Incorrect Pinnacle credentials or proxy issue

**Fix via Claude:**
```
You: "Check the logs for authentication errors"
Claude: [Shows error details]
You: "The password is wrong. Update PINNACLE_PASSWORD to: newpassword123"
Claude: [Updates Railway env var, restarts scraper]
```

### "WebSocket Disconnected"

**Cause:** Session expired or network issue

**Fix:** Scraper auto-recovers via health monitoring. If persistent:
```
You: "Restart the scraper"
Claude: ✅ Restarted
```

### "No Proxy Credit"

**Fix:**
1. Add credit to PacketStream account
2. No config change needed - proxy will work immediately

### "Not Receiving Notifications"

**Fix:**
1. Check you subscribed to correct topic in ntfy app
2. Verify `NTFY_TOPIC` env var matches exactly
3. Ask Claude: `"Send a test notification"`

---

## 📱 Mobile Notifications Setup

### Android

1. Install [ntfy app](https://play.google.com/store/apps/details?id=io.heckel.ntfy)
2. Open app → "+" button
3. Enter your topic name (e.g., `acheron-bob-12345`)
4. Enable notifications for this topic
5. Done! 🎉

### iOS

1. Install [ntfy app](https://apps.apple.com/app/ntfy/id1625396347)
2. Open app → "Add Subscription"
3. Enter topic name
4. Enable Critical Alerts (Settings → Notifications → ntfy → Allow Critical Alerts)
5. Done! 🎉

**Tip:** Set priority 5 alerts to bypass Do Not Disturb mode.

---

## 🔐 Security Best Practices

✅ **Railway encrypts all environment variables**
✅ **Redis is on private network (not exposed to internet)**
✅ **MCP server requires authentication**
✅ **Proxy credentials never logged**

### Protect Your ntfy Topic

Your topic name is like a password. Keep it secret:
- ❌ Don't use `acheron-alerts` (too obvious)
- ✅ Use `acheron-bob-x9k2p5` (unique + random)

Anyone with your topic name can send you notifications!

---

## 📈 Monitoring & Alerts

### Daily Health Checks

Ask Claude:
```
You: "How's the scraper doing?"
Claude: ✅ Uptime: 14 hours
        📊 8,234 odds updates
        🎯 5 arbitrage alerts today
        💾 Memory: 34% used
        💰 Proxy: $7.42 remaining
```

### Automatic System Alerts

You'll receive push notifications for:
- ✅ Scraper started
- 🛑 Scraper stopped
- 🚨 Authentication failures (after 3 attempts)
- 💰 Arbitrage opportunities

---

## 🔄 Updating Code

### Via Claude Code

```
You: "Update to the latest version"
Claude: [Runs: deploy_update()]
        ✅ Pulled latest changes
        ✅ Restarted scraper
```

### Via Railway Dashboard

Railway auto-deploys when you push to GitHub:

1. Make changes locally
2. `git push origin main`
3. Railway rebuilds and redeploys automatically
4. Zero downtime!

---

## 🆘 Getting Help

1. **Check logs first:**
   ```
   You: "Show me the last 50 error logs"
   Claude: [Filters and displays errors]
   ```

2. **Ask Claude to diagnose:**
   ```
   You: "Something's wrong, can you check?"
   Claude: [Runs scraper_status(), view_logs(), system_info()]
           [Provides diagnosis and fix suggestions]
   ```

3. **GitHub Issues:** Report bugs at [github.com/yourusername/Pinnacle-Scrapper/issues](https://github.com)

---

## 🎉 You're All Set!

Your scraper is now:
- ✅ Running 24/7 on Railway
- ✅ Monitoring NHL odds in real-time
- ✅ Sending arbitrage alerts to your phone
- ✅ Fully manageable via English commands to Claude Code

**Just tell Claude what you want, and it handles the rest!**

---

## 📚 Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [PacketStream Docs](https://packetstream.io/documentation)
- [ntfy Documentation](https://ntfy.sh/docs)
- [Project Acheron Technical Spec](./Project_Acheron_Technical_Specification.md)

---

**Questions?** Just ask Claude Code:
```
You: "How do I [task]?"
Claude: [Provides step-by-step guidance]
```
