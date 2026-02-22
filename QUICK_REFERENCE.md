# 🚀 Quick Reference - Managing Acheron via Claude Code

## 📞 How to Talk to Claude

Just use natural English! Here are common commands:

---

## 🎮 Basic Controls

| What You Want | What You Say |
|---------------|--------------|
| Start scraper | "Start the scraper" |
| Stop scraper | "Stop the scraper" |
| Restart scraper | "Restart the scraper" |
| Check if running | "Is it running?" / "Status?" |

---

## 📊 Monitoring

| What You Want | What You Say |
|---------------|--------------|
| System status | "How's it doing?" / "Status report" |
| View alerts | "Show me today's alerts" |
| View logs | "Show me the last 50 logs" |
| Error logs only | "Show me recent errors" |
| Proxy balance | "How much proxy credit left?" |
| Resource usage | "Check CPU and memory usage" |

---

## ⚙️ Configuration

| What You Want | What You Say |
|---------------|--------------|
| Change profit threshold | "Only alert for 3%+ profit" |
| Change bet limit | "Only alert for $1000+ bets" |
| Add more leagues | "Start monitoring KHL too" |
| View current settings | "What are my current settings?" |

---

## 🔧 Troubleshooting

| Problem | What You Say |
|---------|--------------|
| Something's broken | "Something's wrong, can you check?" |
| Not getting alerts | "Why am I not getting notifications?" |
| Too many alerts | "I'm getting too many alerts, reduce them" |
| WebSocket issues | "WebSocket keeps disconnecting, fix it" |

---

## 🔄 Updates & Maintenance

| What You Want | What You Say |
|---------------|--------------|
| Update code | "Update to the latest version" |
| Check for updates | "Is there a new version available?" |
| View changelog | "What's new in the latest version?" |
| Backup config | "Show me my current configuration" |

---

## 📅 Scheduling

| What You Want | What You Say |
|---------------|--------------|
| Stop temporarily | "Stop it for tonight" |
| Stop for days | "Stop it for the next 3 days" |
| Resume later | "Start it back up" |
| Run during games only | "Only run during live games" |

---

## 🔍 Data Queries

| What You Want | What You Say |
|---------------|--------------|
| Today's alerts | "Show me today's arbitrage opportunities" |
| Yesterday's alerts | "What opportunities did I miss yesterday?" |
| Best opportunity | "What was the best arbitrage today?" |
| Alert history | "Show me all alerts from this week" |

---

## 💰 Cost Management

| What You Want | What You Say |
|---------------|--------------|
| Check proxy credit | "How much proxy credit left?" |
| Estimate burn rate | "How long until I need more credit?" |
| Railway costs | "How much am I spending on Railway?" |
| Optimize costs | "How can I reduce costs?" |

---

## 🆘 Emergency Commands

| Emergency | What You Say |
|-----------|--------------|
| Everything's broken | "Help! Everything's broken" |
| Stop immediately | "STOP everything NOW" |
| Reset to defaults | "Reset to default settings" |
| Fresh start | "Restart everything from scratch" |

---

## 💡 Pro Tips

**Be Conversational:**
- ✅ "Is the scraper still running?"
- ✅ "How many alerts did I get today?"
- ✅ "Change the profit threshold to 2.5%"

**Be Specific When Needed:**
- ✅ "Show me alerts from February 20th"
- ✅ "Update min_profit_percent to 3.5"
- ✅ "View the last 100 lines of logs with errors only"

**Ask Follow-up Questions:**
```
You: "Status?"
Claude: ✅ Running for 6 hours, 3 alerts today
You: "Show me those alerts"
Claude: [displays alert details]
You: "What was the best one?"
Claude: Bruins vs Leafs - 3.4% profit at 2:14 PM
```

---

## 🎯 Common Workflows

### Morning Check
```
You: "Good morning, status report please"
Claude: [Full system status + yesterday's summary]
You: "Any good alerts overnight?"
Claude: [Shows overnight alerts]
```

### Adjusting Sensitivity
```
You: "I'm getting too many alerts"
Claude: What threshold would you like? Current is 2%
You: "Make it 3.5%"
Claude: ✅ Updated to 3.5%. Restarting...
```

### Troubleshooting
```
You: "Something seems off, can you diagnose?"
Claude: [Checks all systems]
        ⚠️  Found: WebSocket disconnected 3 times in last hour
You: "Can you fix it?"
Claude: 🔧 Restarting WebSocket connection...
        ✅ Reconnected successfully
```

### Travel Mode
```
You: "I'm traveling for a week, stop the scraper"
Claude: ✅ Stopped. Have a great trip!

[One week later]

You: "I'm back, start it up"
Claude: ✅ Starting scraper...
        ✅ Running! Welcome back!
```

---

## 📱 Notification Settings

### Critical Alerts Only
```
You: "Only send critical alerts (4%+ profit)"
Claude: ✅ Set to 4% minimum
```

### Include More Info
```
You: "Can you include bet amounts in notifications?"
Claude: ✅ Enabled. Alerts will now show:
        - Profit %
        - Recommended bet amounts
        - Max bet limits
```

### Quiet Hours
```
You: "Don't send alerts between 11 PM and 7 AM"
Claude: ✅ Quiet hours set
```

---

## 🔐 Security

### Check Access
```
You: "Who has access to my scraper?"
Claude: Only you via this MCP connection
```

### Rotate Secrets
```
You: "I think my PacketStream key leaked"
Claude: Generate a new key at packetstream.io, then:
You: "Update PACKETSTREAM_API_KEY to [new key]"
Claude: ✅ Updated and restarted
```

---

## 📖 Getting Help

### General Help
```
You: "How do I [anything]?"
Claude: [Explains step by step]
```

### Feature Questions
```
You: "Can the scraper monitor player props?"
Claude: Yes! Here's how to enable it...
```

### Technical Details
```
You: "How does the arbitrage detection work?"
Claude: [Explains the Redis Lua script atomic logic]
```

---

## 🎓 Learn More

- Full setup guide: `RAILWAY_SETUP.md`
- Deployment summary: `DEPLOYMENT_SUMMARY.md`
- Technical docs: `Project_Acheron_Technical_Specification.md`

---

**Remember: Just talk naturally! I understand context and can figure out what you want.** 🚀
