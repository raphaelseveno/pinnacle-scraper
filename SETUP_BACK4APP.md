# 🚀 Back4app Setup Guide (No Credit Card Required!)

Complete setup for Project Acheron on Back4app's free tier.

---

## 📋 **What You'll Need (5 minutes to gather)**

1. **Pinnacle Account** (free, no deposit)
   - Sign up: https://www.ps3838.com/
   - Just need username/password for data access

2. **PacketStream Account** ($10 one-time)
   - Sign up: https://packetstream.io/
   - Add $10 credit (lasts 5-10 months)
   - Get API key from dashboard

3. **ntfy.sh Topic** (free, no signup)
   - Choose unique name: `acheron-yourname`
   - Install app on phone

4. **Upstash Redis** (free, no credit card)
   - Sign up: https://upstash.com/
   - Create free Redis database
   - Get connection details

---

## 🎯 **Step-by-Step Setup**

### **PART 1: Set Up Free Redis (5 minutes)**

We'll use Upstash Redis (free tier) instead of self-hosting to save memory.

1. **Go to Upstash:**
   - Visit: https://upstash.com/
   - Click "Start for Free"
   - Sign up with GitHub or email (NO credit card!)

2. **Create Redis Database:**
   - Click "Create Database"
   - Name: `acheron-redis`
   - Type: **Regional**
   - Region: Choose closest to you
   - TLS: **Enabled**
   - Click "Create"

3. **Get Connection Details:**
   - Click on your database
   - Find and copy:
     - **Endpoint** (looks like: `usw1-xxx.upstash.io`)
     - **Port** (usually `6379` or `33816`)
     - **Password** (click "show" to reveal)

   **SAVE THESE** - you'll need them!

---

### **PART 2: Set Up Back4app (10 minutes)**

1. **Sign Up for Back4app:**
   - Visit: https://www.back4app.com/
   - Click "Start for Free"
   - Sign up with GitHub or email
   - Verify your email
   - **No credit card required!**

2. **Create New App:**
   - Click "Build new app"
   - Choose **"Container as a Service"**
   - App name: `acheron`
   - Click "Create"

3. **Connect GitHub (Recommended):**
   - Click "Connect GitHub"
   - Authorize Back4app
   - Select your `pinnacle-scraper` repository
   - Branch: `main` (or `master`)

   **OR Upload Directly:**
   - Click "Upload Dockerfile"
   - Select `Dockerfile.back4app`

4. **Configure Environment Variables:**

   Click "Settings" → "Environment Variables" → Add these:

   ```
   REDIS_HOST=your-upstash-endpoint.upstash.io
   REDIS_PORT=6379
   REDIS_PASSWORD=your-upstash-password
   ```

5. **Configure Build:**
   - Dockerfile path: `Dockerfile.back4app`
   - Container port: `8080`
   - CPU: `0.25 vCPU` (shared)
   - RAM: `256 MB`

6. **Deploy:**
   - Click "Deploy"
   - Wait 3-5 minutes for build
   - Check logs for status

---

### **PART 3: Configure Acheron (5 minutes)**

Before deploying, edit `config.yaml`:

```yaml
# Pinnacle credentials
pinnacle:
  username: "your_pinnacle_username"
  password: "your_pinnacle_password"

# PacketStream proxy
proxy:
  api_key: "your_packetstream_key"

# Upstash Redis (from Part 1)
redis:
  host: "your-upstash-endpoint.upstash.io"
  port: 6379
  password: "your-upstash-password"

# ntfy.sh notifications
notifications:
  ntfy:
    topic: "acheron-yourname"

# IMPORTANT: Memory optimizations for 256MB
advanced:
  # Reduce memory usage
  max_concurrent_connections: 1
  message_buffer_size: 100
  log_level: "WARNING"  # Reduce logging overhead
```

---

### **PART 4: Monitor & Verify (5 minutes)**

1. **Check Deployment Status:**
   - Go to Back4app dashboard
   - Click on your `acheron` app
   - Check "Logs" tab

2. **Look for Success Messages:**
   ```
   ✅ Configuration loaded
   ✅ Redis connection established (Upstash)
   ✅ Components initialized
   ✅ Test notification sent
   ✅ Authentication successful
   ✅ WebSocket connected
   ✅ PROJECT ACHERON IS RUNNING
   ```

3. **Check Your Phone:**
   - Should receive test notification
   - Subscribe to your ntfy topic if not done

4. **Monitor Memory Usage:**
   ```
   Back4app Dashboard → Metrics → Memory
   ```
   - Should stay under 240MB
   - If hitting limits, see optimization section below

---

## ⚠️ **If You Hit Memory Limits**

Back4app's 256MB is tight. Here's how to optimize:

### **Option 1: Disable Browser Headless Mode Caching**

Edit `config.yaml`:
```yaml
stealth:
  browser:
    headless: true
    disable_dev_shm: true  # Add this
```

### **Option 2: Reduce Tracking Scope**

Track fewer markets to save memory:
```yaml
sports:
  markets:
    - "moneyline"  # Only track this, comment out others

  game_states:
    - "live"  # Only live games, skip pre-game
```

### **Option 3: Use Railway for 30 Days**

If Back4app's 256MB is too limiting:

1. Sign up: https://railway.app/
2. Get $5 credit (30 days, no CC required)
3. Deploy full Docker setup
4. Better resources: 512MB-1GB RAM
5. Use 30 days to find long-term solution

---

## 💰 **Total Cost Breakdown**

| Service | Cost |
|---------|------|
| Back4app | $0 (free forever) |
| Upstash Redis | $0 (free tier) |
| PacketStream | $10 one-time (lasts 5-10 months) |
| ntfy.sh | $0 (free) |
| **Ongoing monthly** | **~$1-2** |

---

## 🔧 **Troubleshooting**

### **Out of Memory Error**

**Symptoms:**
```
Container killed (OOMKilled)
```

**Solutions:**
1. Enable memory optimizations in config
2. Track fewer markets (only moneyline)
3. Use Railway trial instead (better resources)

### **Redis Connection Failed**

**Symptoms:**
```
Failed to connect to Redis
```

**Solutions:**
1. Verify Upstash credentials in environment variables
2. Check Upstash dashboard - database running?
3. Verify TLS is enabled in Upstash settings

### **WebSocket Won't Connect**

**Symptoms:**
```
Failed to connect to WebSocket
```

**Solutions:**
1. Check authentication succeeded first
2. Verify proxy credentials
3. Check PacketStream balance

---

## 🚀 **Alternative: Railway (Better Resources, 30 Days)**

If Back4app's 256MB is too limiting, use Railway's trial:

### **Railway Setup (10 minutes)**

1. **Sign up:** https://railway.app/
2. **Connect GitHub:** Link your repo
3. **New Project → Deploy from GitHub**
4. **Select:** `pinnacle-scraper` repo
5. **Add Redis:** Railway provides Redis free on trial
6. **Environment Variables:** Same as Back4app
7. **Deploy:** Click deploy

**You get:**
- $5 credit (lasts ~30 days)
- 512MB-1GB RAM (much better!)
- Full Docker + Redis support
- No credit card for trial

**After 30 days:** Need to add payment method OR migrate elsewhere

---

## 📊 **Performance Comparison**

| Platform | RAM | CPU | Redis | Cost | CC Required | Verdict |
|----------|-----|-----|-------|------|-------------|---------|
| **Back4app** | 256MB | 0.25 | External | $0 | ❌ NO | Best free option |
| **Railway** | 512MB-1GB | Good | Included | $5/30d | ❌ NO (trial) | Best resources (30d) |
| **Oracle Cloud** | 24GB | 4-core | Self-host | $0 | ✅ YES | Best overall (needs CC) |

---

## ✅ **You're Ready!**

Follow the steps above and you'll have Acheron running on Back4app for **free, without a credit card**.

**Need help?** Drop the error logs and I'll troubleshoot!
