# 🆓 FREE Setup - Mobile Hotspot Method (No Paid Proxy!)

Complete guide to run Project Acheron for **$0/month** using your phone's mobile hotspot.

---

## 💡 **How This Works**

Instead of paying for residential proxies, we use your phone's 4G/5G connection:

1. **You authenticate** via mobile hotspot (on your computer)
2. **Extract cookies** from authenticated session
3. **Upload cookies** to free VPS (Back4app/Railway)
4. **VPS uses cookies** for WebSocket (datacenter IP is fine after auth)

**Total cost:** $0/month (uses ~240MB/month of phone data)

---

## 📋 **What You Need**

### **Free Services (No Credit Card):**
1. ✅ **Back4app** (VPS hosting)
2. ✅ **Upstash** (Redis database)
3. ✅ **ntfy.sh** (notifications)
4. ✅ **Your phone's mobile hotspot** (proxy replacement!)

### **Accounts Needed:**
1. ✅ **Pinnacle account** (free, no deposit)
2. ✅ **Your phone with data plan**

**Total monthly cost: $0** 🎉

---

## 🚀 **Step-by-Step Setup**

### **PART 1: Set Up Free Hosting (15 minutes)**

Follow the **Back4app setup** from `SETUP_BACK4APP.md`:
- Sign up for Back4app (free, no CC)
- Sign up for Upstash Redis (free, no CC)
- Deploy Acheron container

**Skip the proxy configuration** - we'll use mobile hotspot instead!

---

### **PART 2: Configure for Mobile Hotspot (5 minutes)**

Edit `config.yaml` and **comment out proxy section**:

```yaml
# Pinnacle credentials
pinnacle:
  username: "your_pinnacle_username"
  password: "your_pinnacle_password"

# NO PROXY - using mobile hotspot
# proxy:
#   provider: "packetstream"
#   api_key: "..."
#   use_proxy_for:
#     - "authentication"

# Upstash Redis
redis:
  host: "your-upstash-endpoint.upstash.io"
  port: 6379
  password: "your-upstash-password"

# ntfy.sh
notifications:
  ntfy:
    topic: "acheron-yourname"
```

---

### **PART 3: Authenticate via Mobile Hotspot (10 minutes)**

**On your local computer:**

1. **Connect to your phone's mobile hotspot:**
   - iPhone: Settings → Personal Hotspot → Turn On
   - Android: Settings → Network → Mobile Hotspot → Turn On
   - Connect your computer to the hotspot

2. **Install Python (if not installed):**
   - **Mac:** `brew install python@3.11`
   - **Windows:** Download from python.org
   - **Linux:** `sudo apt install python3.11`

3. **Install dependencies:**
   ```bash
   cd "Pinnacle Scrapper"
   pip install -r requirements.txt
   ```

4. **Run authentication script:**
   ```bash
   python scripts/auth_via_mobile.py
   ```

5. **What happens:**
   - Browser opens on your computer
   - Connects to Pinnacle via mobile IP
   - Bypasses Cloudflare (mobile IPs work great!)
   - Saves cookies to `session_data.json`

6. **Output:**
   ```
   ✅ Authentication successful!
   💾 Session data saved to: session_data.json

   📋 Session details:
     - Cookies: 12 cookies
     - WebSocket URL: wss://push.ps3838.com/...
     - Expires in: 1500 seconds
   ```

---

### **PART 4: Upload to VPS (2 minutes)**

**Upload session to Back4app:**

```bash
# Copy session data to VPS
scp session_data.json back4app:/app/

# Or if using Railway
scp session_data.json railway:/app/
```

**Alternatively, paste into environment variable:**
```bash
# On Back4app dashboard:
# Settings → Environment Variables → Add:
SESSION_COOKIES=<paste contents of session_data.json>
```

---

### **PART 5: Modify VPS to Use Saved Cookies (5 minutes)**

We need to modify the VPS deployment to use pre-saved cookies instead of authenticating itself.

Create this file: `src/cookie_loader.py`

```python
"""Load pre-authenticated session cookies"""
import json
from pathlib import Path

def load_session_data():
    """Load session data from file or environment"""

    # Try file first
    session_file = Path('/app/session_data.json')
    if session_file.exists():
        with open(session_file) as f:
            return json.load(f)

    # Try environment variable
    import os
    session_json = os.getenv('SESSION_COOKIES')
    if session_json:
        return json.loads(session_json)

    return None
```

**Then modify `src/main.py`** to skip authentication if cookies exist:

```python
# In main.py, around line 150 (authenticate step):

# Check for pre-loaded session
from cookie_loader import load_session_data
session_data = load_session_data()

if session_data:
    logger.info("✅ Using pre-authenticated session from file")
    self.interceptor.set_session_data(session_data)
else:
    # Normal authentication flow
    logger.info("Step 1/4: Authenticating to Pinnacle...")
    auth_success = await self.scout.authenticate()
    # ... rest of auth code
```

---

### **PART 6: Redeploy VPS (2 minutes)**

```bash
# Push changes
git add .
git commit -m "Add cookie loader for mobile auth"
git push

# Redeploy
# Back4app auto-deploys from GitHub
# Or click "Deploy" in dashboard
```

---

## 📱 **Daily Workflow**

### **Every 25 Minutes (Before Session Expires):**

1. **Connect to mobile hotspot**
2. **Run:** `python scripts/auth_via_mobile.py`
3. **Upload:** `scp session_data.json vps:/app/`
4. **Disconnect from hotspot**

**Time required:** 2 minutes
**Data usage:** ~5MB per auth

---

## 🤖 **Semi-Automation Option**

If you want to reduce manual work:

**Option A: Cron job on your computer**
```bash
# Run every 20 minutes
*/20 * * * * cd ~/pinnacle-scraper && ./scripts/auto_auth.sh
```

**Option B: Keep computer running with mobile hotspot**
- Computer stays connected to hotspot 24/7
- Script auto-authenticates every 20 minutes
- Uploads cookies automatically
- **Cost:** ~7GB/month mobile data

---

## 💰 **Monthly Cost Breakdown**

| Item | Cost |
|------|------|
| Back4app hosting | $0 |
| Upstash Redis | $0 |
| ntfy.sh notifications | $0 |
| Mobile data (~240MB) | $0* |
| **TOTAL** | **$0/month** |

*Assuming you have unlimited data or 240MB fits within your plan

---

## 📊 **Data Usage Calculator**

**Per authentication:**
- Initial page load: ~2MB
- Cloudflare challenge: ~1MB
- Login + cookie extraction: ~2MB
- **Total:** ~5MB

**Monthly usage:**
- 2 auths/day × 30 days = 60 auths
- 60 × 5MB = **300MB/month**

**Fits easily within most mobile plans!**

---

## 🔄 **When to Re-Authenticate**

Sessions expire after **30 minutes**. Re-auth when:

1. **Scheduled:** Every 25 minutes (safe margin)
2. **On error:** If VPS logs show "Session expired"
3. **After disconnect:** If WebSocket drops

---

## ⚡ **Upgrade Path (When Needed)**

If manual re-auth becomes annoying:

### **Option 1: IPRoyal $3.50 (13 months)**
- Buy 2GB residential proxies
- Fully automate authentication
- VPS handles everything
- No more manual work

### **Option 2: PacketStream $50 (7 months)**
- When arbitrage is profitable
- Better proxy quality
- Professional setup

---

## ❓ **FAQ**

### **Q: Can I use WiFi instead of mobile hotspot?**
**A:** Only if it's YOUR home WiFi (residential IP). Public WiFi won't work (datacenter IP).

### **Q: What if I don't have unlimited data?**
**A:** 300MB/month is very small. Most plans have 1GB+ these days.

### **Q: Can I automate this completely?**
**A:** Not for free. You'd need to buy residential proxies ($3.50+) for full automation.

### **Q: Does this work with VPN?**
**A:** No! VPNs use datacenter IPs. Must be direct mobile/home connection.

### **Q: How reliable is this?**
**A:** Mobile IPs have 85-95% success against Cloudflare. Very reliable!

---

## 🎉 **Summary**

**You can run Project Acheron for $0/month** using this method:

✅ Free VPS (Back4app)
✅ Free Redis (Upstash)
✅ Free proxy (your phone!)
✅ Free notifications (ntfy.sh)

**Trade-off:** 2 minutes of manual work every 25 minutes

**Perfect for:**
- Testing the system
- Low-volume usage
- Before investing in paid proxies
- Proof of concept

**Ready to start?** Follow Part 1 and set up Back4app!
