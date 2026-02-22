# Project Acheron ⚡

**Real-time NHL odds scraping and arbitrage detection on a near-zero budget**

Acheron is an autonomous system that hijacks Pinnacle's WebSocket connection to receive real-time NHL odds updates with <500ms latency, performs atomic arbitrage detection using Redis/Lua, and sends instant push notifications to your phone - all for **$1-2/month**.

---

## 🚀 NEW: One-Click Railway Deployment

**Deploy in 5 minutes with English-language management via Claude Code!**

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/acheron)

✅ No VPS setup required
✅ Fully managed by talking to Claude Code in English
✅ $5/month (first month free)
✅ Auto-scaling and monitoring included

👉 **[See Railway Setup Guide](./RAILWAY_SETUP.md)** for step-by-step instructions

---

## 🎯 Features

- ⚡ **Sub-500ms latency** - Direct WebSocket hijacking for institutional-grade speed
- 🤖 **Fully autonomous** - Self-healing architecture with automatic re-authentication
- 💰 **Near-zero cost** - $1-2/month using Oracle Cloud Free Tier + minimal proxy
- 🔒 **Stealth authentication** - Nodriver + Cloudflare Turnstile bypass
- 🎲 **Atomic arbitrage** - Redis Lua scripts eliminate race conditions
- 📱 **Critical alerts** - ntfy.sh push notifications (bypasses silent mode)
- 🏒 **NHL focused** - Optimized for hockey, expandable to other sports

---

## 💵 Cost Breakdown

| Component | Service | Monthly Cost |
|-----------|---------|--------------|
| **VPS** | Oracle Cloud Free Tier | $0 |
| **Proxy** | PacketStream (10-50MB/month) | $1-2 |
| **Redis** | Self-hosted on VPS | $0 |
| **Notifications** | ntfy.sh | $0 |
| **TOTAL** | | **$1-2/month** |

*PacketStream: $10 prepaid credit lasts 5-10 months at low usage rate*

---

## ⚙️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  ORACLE CLOUD FREE TIER (4-core ARM, 24GB RAM)        │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Scout (Nodriver)                                  │ │
│  │ - Cloudflare Turnstile bypass                     │ │
│  │ - Session cookie extraction                       │ │
│  └───────────────┬───────────────────────────────────┘ │
│                  ▼                                      │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Interceptor (WebSocket)                           │ │
│  │ - Real-time odds stream (<500ms latency)          │ │
│  │ - Auto-reconnect with exponential backoff         │ │
│  └───────────────┬───────────────────────────────────┘ │
│                  ▼                                      │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Engine (Redis + Lua)                              │ │
│  │ - Atomic arbitrage detection                      │ │
│  │ - Zero race conditions                            │ │
│  └───────────────┬───────────────────────────────────┘ │
│                  ▼                                      │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Notifier (ntfy.sh)                                │ │
│  │ - Priority 5 alerts (critical)                    │ │
│  │ - Deep links to bet slip                          │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
         │                              │
         │ Auth via Proxy               │ WebSocket Direct
         ▼                              ▼
    PacketStream                    Pinnacle
    Residential Proxy               wss://push.ps3838.com
```

---

## 🚀 Quick Start (3 Steps)

### 1. Sign Up for Free Services (10 minutes)

**Oracle Cloud Free Tier** (VPS):
- Go to https://signup.oraclecloud.com/
- Create account (requires credit card for verification, NOT charged)
- Create Ubuntu 22.04 ARM VM: 4 OCPU, 24GB RAM

**PacketStream** (Residential Proxy):
- Go to https://packetstream.io/
- Sign up and purchase $10 credit (lasts 5-10 months)
- Copy your API key from dashboard

**ntfy.sh** (Notifications):
- No signup needed!
- Just choose a unique topic name (e.g., `acheron-alerts-yourname`)

---

### 2. Deploy to Oracle Cloud (30 minutes)

**SSH into your Oracle VPS:**
```bash
ssh ubuntu@<your-oracle-ip>
```

**Run automated setup:**
```bash
curl -fsSL https://raw.githubusercontent.com/[your-repo]/main/scripts/setup_oracle.sh | bash
```

**Log out and back in** (for Docker permissions):
```bash
exit
ssh ubuntu@<your-oracle-ip>
```

**Clone/upload project files:**
```bash
cd ~
# Option A: If pushing to GitHub
git clone https://github.com/[your-repo]/pinnacle-scraper.git
cd pinnacle-scraper

# Option B: Upload from local machine (run on your computer)
scp -r /path/to/pinnacle-scraper ubuntu@<your-oracle-ip>:~/
ssh ubuntu@<your-oracle-ip>
cd pinnacle-scraper
```

---

### 3. Configure and Launch (10 minutes)

**Edit configuration file:**
```bash
nano config.yaml
```

**Fill in your credentials:**
```yaml
pinnacle:
  username: "your_ps3838_username"  # REQUIRED
  password: "your_ps3838_password"  # REQUIRED

proxy:
  api_key: "your_packetstream_api_key"  # REQUIRED

notifications:
  ntfy:
    topic: "acheron-alerts-yourname"  # Choose unique name
```

Save and exit (`Ctrl+X`, `Y`, `Enter`)

**Deploy with one command:**
```bash
./scripts/deploy.sh
```

**Done!** 🎉

The system is now running autonomously. Check your phone - you should receive a test notification.

---

## 📱 Receiving Alerts

**On Android:**
1. Install ntfy.sh app: https://play.google.com/store/apps/details?id=io.heckel.ntfy
2. Add subscription: `acheron-alerts-yourname` (your topic from config)
3. Enable notifications
4. Done! Critical alerts will bypass silent mode.

**On iPhone:**
1. Install ntfy.sh app: https://apps.apple.com/app/ntfy/id1625396347
2. Add subscription: `acheron-alerts-yourname`
3. Enable critical alerts in iOS settings
4. Done!

**Web (no app):**
- Visit: https://ntfy.sh/acheron-alerts-yourname

---

## 🛠️ Management Commands

**View logs:**
```bash
docker-compose logs -f acheron
```

**Check status:**
```bash
docker-compose ps
```

**Restart services:**
```bash
docker-compose restart
```

**Stop services:**
```bash
docker-compose down
```

**Update code and restart:**
```bash
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

---

## 📊 Monitoring

**Check system health:**
```bash
docker-compose logs acheron | grep "System Status"
```

**View arbitrage statistics:**
```bash
docker-compose logs acheron | grep "Engine:"
```

**WebSocket connection status:**
```bash
docker-compose logs acheron | grep "WebSocket"
```

**Redis health:**
```bash
docker-compose exec redis redis-cli ping
```

---

## ⚠️ Troubleshooting

### Authentication fails
**Symptoms:** "Authentication failed" in logs

**Solutions:**
1. Verify Pinnacle credentials in `config.yaml`
2. Check proxy is working: `docker-compose logs acheron | grep "proxy"`
3. Try rotating proxy (wait 5 minutes and restart)

### WebSocket won't connect
**Symptoms:** "Failed to connect to WebSocket"

**Solutions:**
1. Check if authentication succeeded first
2. Verify session cookies were extracted: `docker-compose logs acheron | grep "cookie"`
3. Check if datacenter IP is blocked (may need to enable proxy for WebSocket)

### No arbitrage alerts
**Symptoms:** System running but no alerts

**Solutions:**
1. This is normal! Arbitrage opportunities are rare
2. Lower threshold in config: `min_profit_percent: 1.0` (instead of 2.0)
3. Check engine is processing odds: `docker-compose logs acheron | grep "odds_updates"`

### Cloudflare Turnstile blocks authentication
**Symptoms:** "Cloudflare challenge not completed"

**Solutions:**
1. Wait 10 minutes (Turnstile has cooldown)
2. Rotate proxy IP
3. Try non-headless mode (edit Dockerfile, set `headless: false`)

### Oracle Cloud VPS terminated
**Symptoms:** Can't SSH into server

**Oracle may terminate if:**
- Account looks fraudulent (use real info)
- Excessive bandwidth (stay under 1TB/month)
- CPU mining detected (we're not doing this)

**Backup plan:**
- Use AWS $200 credit (6 months free)
- Use Google Cloud $300 credit (3 months free)

---

## 📈 Optimization Tips

### Reduce bandwidth usage:
```yaml
sports:
  markets:
    - "moneyline"  # Only track moneyline (not puckline, totals)

  game_states:
    - "live"  # Only live games (not pre-game)
```

### Increase alert sensitivity:
```yaml
notifications:
  thresholds:
    min_profit_percent: 1.0  # Alert on 1%+ arbs (default: 2%)
    min_bet_limit: 100  # Lower minimum bet size (default: $500)
```

### Add more leagues:
```yaml
sports:
  leagues:
    - "NHL"
    - "KHL"  # Add Russian league
    - "AHL"  # Add American league
```

---

## 🔒 Security & Privacy

### What data is collected?
- **By Pinnacle:** Your login activity (same as using their website)
- **By PacketStream:** Proxy usage logs
- **By ntfy.sh:** Notification metadata (no message content stored)
- **By us:** Nothing. All data stays on your VPS.

### Is this legal?
- Scraping violates Pinnacle's Terms of Service (account ban risk)
- NOT illegal in criminal law sense
- Use at your own risk

### Protecting your account:
- Use residential proxy for all auth (enabled by default)
- Don't use datacenter IP for authentication
- Don't run multiple instances from same proxy
- Accept that bans may happen (use test accounts with minimal funds)

---

## 🤝 Contributing

This project is for educational purposes. Contributions welcome:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📜 License

This project is provided "as-is" for educational purposes only.

**Disclaimer:**
- Using this software violates Pinnacle's Terms of Service
- Account bans and fund forfeiture may occur
- Author is not responsible for any losses
- Use at your own risk

---

## 🙏 Acknowledgments

- **Nodriver** - Undetected browser automation
- **Redis** - Lightning-fast in-memory database
- **ntfy.sh** - Free push notifications
- **Oracle Cloud** - Forever free VPS
- **PacketStream** - Affordable residential proxies

---

## 📞 Support

**Issues?**
- Check logs: `docker-compose logs acheron`
- Review troubleshooting section above
- Open GitHub issue with logs

**Questions?**
- Read the PRD: `Project_Acheron_Technical_Specification.md`
- Check config comments in `config.yaml`

---

## 🎓 Learning Resources

Want to understand how this works?

- **WebSocket Protocol:** https://datatracker.ietf.org/doc/html/rfc6455
- **Redis Lua Scripting:** https://redis.io/docs/manual/programmability/eval-intro/
- **Browser Fingerprinting:** https://abrahamjuliot.github.io/creepjs/
- **Cloudflare Turnstile:** https://developers.cloudflare.com/turnstile/

---

**Built with ❤️ for the budget-conscious arbitrageur**

*Remember: The house always wins... unless you engineer around it.*
