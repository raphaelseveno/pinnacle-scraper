# Project Acheron: Technical Specification and Research Report for Low-Latency, Low-Budget Sports Data Acquisition

## 1. Executive Summary

In the high-frequency domain of algorithmic sports trading, information is the sole currency. The profitability of arbitrage strategies—simultaneously betting on all outcomes of an event to guarantee profit regardless of the result—is strictly governed by latency. Institutional syndicates leverage direct cross-connects and six-figure API licensing agreements to achieve update speeds of under 50 milliseconds. Conversely, the retail sector is structurally disadvantaged by a "Latency Tax," relying on delayed polling APIs that result in "Ghost Arbs"—opportunities that appear valid on screen but have vanished in reality.

This report presents Project Acheron, a comprehensive technical blueprint and Product Requirement Document (PRD) designed to democratize access to institutional-grade data. Based on the "Grey Market" methodologies outlined in sections 5 through 6.3 of the foundational research, this architecture circumvents the financial barriers of the "White Market." By substituting capital expenditure with technical sophistication—specifically utilizing Nodriver for asynchronous browser automation, WebSocket interception for real-time data "push," and Redis Lua scripting for atomic state management—Project Acheron synthesizes a sub-second latency feed for Pinnacle (PS3838) odds.

Crucially, this system is engineered for a "really, really low budget," defined as an operational cost of under $20 per month. This is achieved through a "Direct + Proxy" hybrid routing strategy that minimizes bandwidth costs and a microservices architecture optimized for low-cost VPS providers like Hetzner.

---

## 2. The Economic Landscape: The Latency Tax and the Grey Market

To understand the technical requirements of Project Acheron, one must first appreciate the economic constraints that necessitate its creation. The sports betting market involves a stratification of data access that effectively excludes low-budget actors from profitability through official channels.

### 2.1 The Data Paradox

The "Data Paradox" defines the 2026 landscape: the data required to guarantee risk-free profit is priced to exclude the very participants who need that guarantee the most. "Sharp" bookmakers like Pinnacle and the Betfair Exchange act as the market's "source of truth." Their odds reflect the most efficient aggregation of information. However, accessing this truth in real-time is prohibitively expensive.

| Data Tier | Access Method | Latency | Monthly Cost | Primary User |
|---|---|---|---|---|
| Institutional | Direct WebSocket / Cross-Connect | < 50ms | > $3,000 | Syndicates, HFT Firms |
| Commercial | Aggregator API (Push) | 200ms - 1s | $100 - $500 | Pro-tail Bettors |
| Retail (Standard) | Public API (Polling) | 30s - 60s | Free - $30 | Casual Bettors |
| Grey Market (Acheron) | Hijacked WebSocket | < 500ms | < $20 | Engineer-Bettors |

The "Retail Tier" relies on REST APIs that require polling. Even with a polling interval of 1 second, the overhead of the HTTP handshake, server processing, and rate limits introduces a delay that renders the data stale for arbitrage. The institutional tier uses persistent WebSocket connections that "push" data updates instantly (deltas). Project Acheron aims to replicate this "push" capability without the institutional price tag.

### 2.2 The "Grey Market" Solution

The "Grey Market" is an ecosystem of unauthorized data acquisition strategies. It is not illegal in the sense of criminal law, but it violates the Terms of Service (ToS) of bookmakers. It leverages the fact that bookmakers must send real-time data to their own web frontends to service regular customers. Project Acheron intercepts this data stream.

The viability of this approach rests on the "Direct + Proxy" model. Residential proxies (IPs assigned to home users) are necessary to bypass anti-bot protections but are expensive ($10/GB). Datacenter IPs (Hetzner, AWS) are cheap but easily blocked. The architecture defined in this report strictly separates traffic to optimize this cost-benefit ratio.

---

## 3. Product Requirement Document (PRD): Project Acheron

- **Version:** 1.0.0
- **Status:** Approved for Development
- **Budget Cap:** $20.00 / month

### 3.1 System Overview

Project Acheron is a distributed microservices system designed to run on a single Debian-based Virtual Private Server (VPS). It consists of three primary components:

1. **The Scout:** A browser automation module using Nodriver to handle authentication and session maintenance.
2. **The Interceptor:** A Python-based WebSocket client that replicates the bookmaker's connection to receive live odds.
3. **The Engine:** A Redis database running Lua scripts for atomic arbitrage detection and state management.

### 3.2 User Personas

- **The Operator:** A technically literate bettor with a limited bankroll. They require immediate notification of arbitrage opportunities to manually place bets via mobile. They cannot afford commercial API subscriptions and prioritize low operating costs over ease of use.

### 3.3 Functional Requirements

#### 3.3.1 FR-01: Stealth Session Initialization

**Description:** The system must initialize a valid web session with Pinnacle (PS3838) that bypasses Cloudflare Turnstile and Akamai bot protections without human intervention.

**Source:** Document Section 5.1.

- **REQ-01.1:** The system MUST use Nodriver (asynchronous Chrome DevTools Protocol wrapper) or Camoufox (stealth Firefox) to launch the browser. Standard Selenium WebDriver is strictly prohibited due to fingerprint leaks (`navigator.webdriver`).
- **REQ-01.2:** The system MUST detect the presence of Cloudflare Turnstile iframes and utilize Nodriver's internal logic or simulated mouse movements (Bezier curves) to solve the challenge.
- **REQ-01.3:** The system MUST extract the `cf_clearance` cookie and the authenticated session token (`ASP.NET_SessionId` or custom JWT) upon successful login.
- **REQ-01.4:** Session tokens MUST be stored in Redis with a Time-To-Live (TTL) matching the cookie's expiration (typically 30 minutes).

#### 3.3.2 FR-02: State Injection and Data Extraction

**Description:** The system must extract the initial odds state directly from the browser's JavaScript memory, avoiding brittle HTML DOM scraping.

**Source:** Document Section 5.2.

- **REQ-02.1:** The system MUST inject a JavaScript snippet using `tab.evaluate()` to access the application's global state store (e.g., Redux `window.store.getState()`, React Context, or `window.__INITIAL_STATE__`).
- **REQ-02.2:** The extraction logic MUST normalize odds into a standard Decimal format (e.g., 2.50) and map generic IDs to human-readable Team Names.
- **REQ-02.3:** If memory injection is blocked, the system MUST fallback to intercepting the `Network.responseReceived` event via CDP to capture the initial JSON payload.

#### 3.3.3 FR-03: WebSocket Replication ("The Push")

**Description:** The system must maintain a persistent, low-latency WebSocket connection to the bookmaker's server to receive real-time updates.

**Source:** Document Section 5.3.

- **REQ-03.1:** The system MUST utilize `aiohttp` or `websockets` (Python libraries) to initiate a WSS connection to the endpoint identified during the browser session (e.g., `wss://push.ps3838.com/...`).
- **REQ-03.2:** The WebSocket handshake MUST replicate the exact headers of the browser session, including `User-Agent`, `Origin`, `Sec-WebSocket-Key`, and the Authorization token extracted in REQ-01.3.
- **REQ-03.3:** The system MUST implement a heartbeat mechanism, sending "Ping" frames (Opcode 0x9) or JSON keep-alive messages at the server-defined interval (typically 25 seconds) to prevent disconnection (Close Code 1006).

#### 3.3.4 FR-04: Atomic Arbitrage Detection

**Description:** The system must identify arbitrage opportunities with zero processing latency using atomic database operations.

**Source:** Document Section 6.3.

- **REQ-04.1:** The system MUST use Redis Hashes to store the current odds for every active market.
- **REQ-04.2:** Arbitrage calculations MUST be performed via Lua Scripts executed directly on the Redis server. This ensures that the "Read-Calculate-Write" cycle is atomic, preventing race conditions where odds change during processing.
- **REQ-04.3:** The Lua script MUST compare the new Pinnacle odds against cached "Soft Book" odds and return an alert payload only if the implied probability sum is < 1.0.

#### 3.3.5 FR-05: Infrastructure and Routing (Cost Control)

**Description:** The system must operate within a <$20/month budget by optimizing traffic routing.

**Source:** Document Section 6.

- **REQ-05.1:** The system MUST be deployed on a Hetzner Cloud VPS (CPX11 or similar) to leverage low-latency peering with European betting servers.
- **REQ-05.2:** The system MUST implement a "Direct + Proxy" hybrid routing strategy.
  - **High-Risk Traffic:** Initial authentication and Cloudflare solving must route through Residential Proxies.
  - **Volume Traffic:** The persistent WebSocket connection and soft-book polling must route through the Direct VPS IP (Datacenter) to save bandwidth costs.
- **REQ-05.3:** The system MUST block all media assets (images, fonts, CSS) at the network level to minimize data usage.

#### 3.3.6 FR-06: High-Priority Notification

**Description:** The system must deliver alerts to the user's mobile device with "Critical" priority to bypass silent modes.

**Source:** Document Section 7.

- **REQ-06.1:** The system MUST utilize the ntfy.sh API for push notifications.
- **REQ-06.2:** Alerts MUST include a `Priority: 5` header to trigger high-priority interruption on Android/iOS.
- **REQ-06.3:** Alerts MUST include "Click Actions" deep-linking directly to the specific event/betslip on the Pinnacle mobile site.

---

## 4. Technical Implementation & Research Deep Dive

This section expands on the PRD requirements, providing the deep technical context, code logic, and architectural reasoning necessary for implementation.

### 4.1 Anti-Bot Infrastructure: The Move to Nodriver

The era of simple `requests` or `BeautifulSoup` scripts is over. Sharp bookmakers utilize advanced bot detection suites (Cloudflare Turnstile, Akamai) that analyze the TLS fingerprint, JavaScript execution environment, and mouse behavior.

#### 4.1.1 Why Selenium Fails

Standard Selenium WebDriver is easily fingerprinted. It injects a globally accessible variable `navigator.webdriver = true` into the browser's JavaScript context. Anti-bot scripts check for this variable immediately upon page load. Furthermore, the communication between the WebDriver binary and the browser creates a distinct latency signature and network traffic pattern that heuristic models can identify.

#### 4.1.2 The Nodriver Advantage

Nodriver (and its predecessor undetected-chromedriver) bypasses the WebDriver protocol entirely. It communicates directly with the browser via the **Chrome DevTools Protocol (CDP)**.

- **Mechanism:** CDP is the native debugging protocol used by Chrome's own DevTools. It allows for instrumentation without injecting the `navigator.webdriver` flag.
- **Asynchronous Design:** Nodriver is built on Python's `asyncio`. This is critical for Project Acheron because the "Scout" service needs to manage the browser session while simultaneously listening to the WebSocket feed. A blocking synchronous library (like standard Selenium) would cause the WebSocket heartbeat to fail during page navigation.

**Implementation Detail (Python/Nodriver):**

```python
import nodriver as uc
import asyncio

async def start_session():
    # FR-01.1: Initialize without WebDriver leaks
    browser = await uc.start(
        headless=False,  # Headless is often a flag; use XVFB on server
        browser_args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
    )
    page = await browser.get('https://www.ps3838.com')

    # FR-01.2: Cloudflare Turnstile handling is often native in Nodriver,
    # but may require explicit wait/find logic if the iframe loads slowly.
    await page.wait_for('div[class*="content"]', timeout=15)

    # FR-01.3: Extract Cookies for the Listener
    cookies = await browser.cookies.get_all()
    # Save to Redis...
```

### 4.2 Data Extraction: The React/Redux Injection

Scraping HTML is computationally expensive and fragile. A minor CSS change by the bookmaker breaks the scraper. The superior "Grey Market" strategy outlined in Section 5.2 is **JavaScript State Injection**.

#### 4.2.1 Accessing the Redux Store

Single Page Applications (SPAs) maintain their state in a client-side database (Redux Store) before rendering it to the DOM. This state contains the raw data: precise decimal odds, event IDs, and market limits.

**The Technique:** Using Nodriver's `tab.evaluate()`, we inject a script to retrieve this state. If the site exposes the store globally (rare in 2026), we access `window.store.getState()`. More commonly, we must access the internal React props of the DOM root.

**JavaScript Injection Payload:**

```javascript
// FR-02.1: React Fiber Traversal
function getReactState() {
    const root = document.querySelector('#root'); // Application entry point
    const key = Object.keys(root).find(k => k.startsWith('__reactContainer'));
    const internalInstance = root[key];

    // Traverse the fiber tree to find the provider with the store
    let child = internalInstance.child;
    while (child) {
        if (child.memoizedProps && child.memoizedProps.store) {
            return child.memoizedProps.store.getState();
        }
        child = child.child;
    }
    return null;
}
return getReactState();
```

This script returns the entire odds database as a JSON object, which Python can parse instantly. This method is orders of magnitude faster than parsing HTML and provides data (like max bet limits) that may not be rendered on screen.

### 4.3 The "Push" Architecture: WebSocket Hijacking

Polling the API is the source of the "Latency Tax." To remove it, we must clone the bookmaker's own socket connection.

#### 4.3.1 Identifying the Endpoint

In the Chrome Network tab (filtered by "WS"), one can observe the connection upgrade (Status 101). The URL typically follows a pattern like `wss://push.ps3838.com/socket.io/?EIO=4&transport=websocket`.

#### 4.3.2 Replicating the Handshake

The server validates the connection based on the HTTP headers sent during the Upgrade handshake.

- **Sec-WebSocket-Key:** A random base64 string (client-generated).
- **Cookie:** Must contain the `ASP.NET_SessionId` and `cf_clearance` obtained by the Scout.
- **User-Agent:** Must match the Scout's UA exactly.

**Python Implementation (aiohttp):**

```python
import aiohttp

# FR-03.2: Replicating headers
headers = {
    "User-Agent": user_agent_from_nodriver,
    "Origin": "https://www.ps3838.com",
    "Cookie": cookie_string_from_redis
}

async with session.ws_connect(websocket_url, headers=headers) as ws:
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            data = json.loads(msg.data)
            # Handle Odds Delta
            await process_delta(data)
```

#### 4.3.3 The Heartbeat Requirement

WebSocket connections are stateful. To keep the connection alive, the client must send a "Heartbeat" or "Ping." The protocol (RFC 6455) defines Opcode 0x9 for Pings, but many implementations (like Socket.io) use a specific application-level message, such as `2` (Ping) and expect `3` (Pong). The research highlights that failing to send this heartbeat every ~25 seconds will result in a server-side disconnect (Code 1006).

### 4.4 Atomic Arbitrage Detection via Redis

Speed is irrelevant if the calculation logic introduces race conditions. Reading odds from a database into Python, checking the arb, and then writing back takes time—during which the odds may change again.

#### 4.4.1 The Role of Redis

Redis is an in-memory key-value store. It is single-threaded, meaning commands are executed sequentially. This property is exploited using **Lua Scripting** to create atomic operations.

#### 4.4.2 The Lua Script Logic

The script performs the "Check-And-Set" logic entirely within the Redis memory space. This is the "Brain" of Project Acheron.

**Script Logic (`check_arb.lua`):**

```lua
-- FR-04.2: Atomic Execution
local market_key = KEYS[1]  -- e.g., "odds:12345:1x2"
local home_odd = tonumber(ARGV[1])
local away_odd = tonumber(ARGV[2])

-- 1. Update Pinnacle Odds
redis.call('HSET', market_key, 'home', home_odd, 'away', away_odd, 'ts', ARGV[3])

-- 2. Check cached Soft Book odds (from a separate scraper)
local soft_key = "soft:" .. market_key
local soft_home = tonumber(redis.call('HGET', soft_key, 'home'))
local soft_away = tonumber(redis.call('HGET', soft_key, 'away'))

if soft_home and soft_away then
    -- 3. Calculate Implied Probability (Arb Detection)
    -- Scenario A: Pinny Home vs Soft Away
    local prob_a = (1/home_odd) + (1/soft_away)
    if prob_a < 1.0 then
        return "ARB_FOUND: " .. prob_a
    end
end

return nil
```

By using `EVAL`, this entire block runs as a single instruction. No other odds update can occur in the middle of the calculation, guaranteeing the integrity of the arbitrage signal.

---

## 5. Infrastructure and Cost Analysis

The prompt specifies a "really really low budget." This constraint dictates the infrastructure choices.

### 5.1 Server: Hetzner Cloud

Section 6.1 of the research identifies Hetzner as the optimal host.

- **Peering:** Hetzner's data centers in Falkenstein (DE) and Helsinki (FI) have direct peering agreements with major European internet exchanges (DE-CIX), providing low-latency routes to the servers of UK and European bookmakers (often hosted in London or Gibraltar).
- **Pricing:** A CPX11 instance (2 vCPU, 2GB RAM, 40GB NVMe) costs ~€4.35/month. This is significantly cheaper than AWS t3.small instances (~$15/month + bandwidth).

### 5.2 The Hybrid Routing Model

This is the most critical component for budget adherence.

- **The Problem:** Datacenter IPs (Hetzner) are banned by Pinnacle. Residential Proxies work but cost $10-$15 per GB.
- **The Solution (Section 6.2):** A "Direct + Proxy" architecture.
  1. **Authentication (Proxy):** The "Scout" uses the residential proxy to load the login page and solve the Cloudflare challenge. Data usage: ~5MB per session.
  2. **WebSocket (Direct):** Once the `cf_clearance` cookie is obtained, the "Listener" attempts to connect to the WebSocket using the Direct VPS IP.
     - **Why this works:** Often, the anti-bot protection validates the cookie (the proof of work), not just the IP. If the cookie is valid, the WSS connection is allowed from a datacenter IP. This drastically reduces proxy bandwidth usage from gigabytes (streaming odds) to megabytes (session tokens).

### Budget Breakdown

| Component | Provider | Specs | Monthly Cost |
|---|---|---|---|
| Server | Hetzner Cloud | CPX11 (ARM64) | €4.35 (~$4.80) |
| Proxy | PacketStream / Reseller | 1GB Residential Traffic | $10.00 |
| Notifications | ntfy.sh | Free Tier | $0.00 |
| Database | Redis | Self-Hosted | $0.00 |
| **Total** | | | **~$14.80** |

This meets the <$20 requirement while maintaining institutional-grade capabilities.

---

## 6. Notification System: ntfy.sh

The final mile of the system is the delivery of the alert. Section 7 of the research highlights ntfy.sh as a superior alternative to Telegram bots or Pushover for low-budget implementations.

### 6.1 Implementation Details

- **Protocol:** Simple HTTP POST. No complex SDKs required.
- **Urgency:** The system sets the `Priority: 5` header. On Android/iOS, this triggers a "Critical Alert," bypassing the user's "Do Not Disturb" or Silent mode settings. This is crucial for arbitrage, where opportunities last seconds.
- **Actionability:** The alert utilizes the `Click` parameter to provide a deep link.
  - Example: `Click: https://www.ps3838.com/sports/soccer/leagues/1234/events/5678`
  - When the user taps the notification, the browser opens directly to the betting market, saving navigation time.

**Python Notification Code:**

```python
import requests

def send_arb_alert(profit, home_odd, away_odd, url):
    requests.post(
        "https://ntfy.sh/my_secret_topic_archer",
        data=f"Profit: {profit}%\nPinny: {home_odd} | Soft: {away_odd}",
        headers={
            "Title": "🔥 ARB DETECTED",
            "Priority": "5",       # Max priority
            "Tags": "moneybag,warning",
            "Click": url           # Deep link
        }
    )
```

---

## 7. Implementation Roadmap

### Phase 1: The Scanner (Days 1-2)

- **Goal:** Successfully scrape PS3838 and output live odds to the console.
- **Action:** Set up the Hetzner VPS. Install Python 3.11 and Nodriver. Write the script to navigate to PS3838 and verify that Cloudflare Turnstile is passed using the residential proxy. Implement the JS injection to dump `window.initialState`.

### Phase 2: The Socket (Days 3-4)

- **Goal:** Maintain a persistent connection without the full browser overhead.
- **Action:** Analyze the WS frames in Chrome DevTools. Identify the handshake headers. Write the `aiohttp` client to replicate the handshake using the cookies from Phase 1. Implement the Heartbeat logic (Ping/Pong every 25s). Verify stability > 6 hours.

### Phase 3: The Engine (Days 5-6)

- **Goal:** Connect Redis and implement Atomic Logic.
- **Action:** Install Redis. Write the Lua scripts for HSET and Arb calculation. Implement the "Direct + Proxy" routing class in Python to manage the traffic split.

### Phase 4: Integration (Day 7)

- **Goal:** End-to-End Alerting.
- **Action:** Connect ntfy.sh. Configure the deep links. Run the system live on low-liquidity markets (e.g., Table Tennis) to test the speed of the alerts.

---

## 8. Conclusion

Project Acheron demonstrates that the barrier to entry for high-speed sports data is not strictly financial; it is technical. By moving from a "consumer" mindset (buying APIs) to an "engineer" mindset (reverse-engineering infrastructure), a low-budget operator can replicate the data capabilities of an institutional firm.

The architecture proposed—leveraging Nodriver for access, WebSockets for speed, Redis for atomicity, and ntfy.sh for delivery—creates a system that is robust, incredibly fast (<500ms latency), and economically efficient (<$15/month). While the "Grey Market" nature of the project carries inherent risks of account bans and maintenance overhead, it remains the only viable path for the budget-constrained arbitrageur in the algorithmic landscape of 2026.

This report provides the complete blueprint for realizing that capability.

---

## Sources

1. Low-Budget Arbitrage Data Access.pdf
2. [Python Web Scraping Using Proxies - PacketStream](https://packetstream.io/python-web-scraping-using-proxies/)
3. [Web Scraping with JavaScript - Hacker News](https://news.ycombinator.com/item?id=24898016)
4. [While debugging, can I have access to the Redux store from the browser console? - Stack Overflow](https://stackoverflow.com/questions/34373462/while-debugging-can-i-have-access-to-the-redux-store-from-the-browser-console)
5. [How to Implement Heartbeat/Ping-Pong in WebSockets - OneUptime](https://oneuptime.com/blog/post/2026-01-27-websocket-heartbeat/view)
6. [How to Fix "Connection Closed Abnormally" WebSocket Errors - OneUptime](https://oneuptime.com/blog/post/2026-01-24-websocket-connection-closed-abnormally/view)
7. [How to Write Redis Lua Scripts for Atomic Operations - OneUptime](https://oneuptime.com/blog/post/2026-01-21-redis-lua-scripts-atomic-operations/view)
8. [Redis Lua script implementing CAS (check-and-set)? - Stack Overflow](https://stackoverflow.com/questions/36441734/redis-lua-script-implementing-cas-check-and-set)
9. [Hetzner Cloud VPS Pricing Calculator (Feb 2026) - CostGoat](https://costgoat.com/pricing/hetzner)
10. [ntfy.sh | Send push notifications to your phone via PUT/POST](https://ntfy.sh/)
11. [Sending messages - ntfy docs](https://docs.ntfy.sh/publish/)
