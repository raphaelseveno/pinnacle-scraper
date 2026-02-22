--[[
Project Acheron - Atomic Arbitrage Detection
Redis Lua Script for zero-latency, race-condition-free arbitrage checking

This script runs ATOMICALLY on the Redis server, ensuring that:
1. Read current odds
2. Calculate arbitrage
3. Return alert payload
...all happen as a single operation (no other commands can interleave)

Usage from Python:
    result = redis.eval(lua_script, 2, pinnacle_key, soft_key, home_odd, away_odd, timestamp)
]]--

-- Input parameters
local pinnacle_key = KEYS[1]  -- e.g., "odds:pinnacle:nhl:12345:moneyline"
local soft_key = KEYS[2]      -- e.g., "odds:bet365:nhl:12345:moneyline"

local home_odd = tonumber(ARGV[1])  -- New Pinnacle home odds (decimal, e.g., 2.15)
local away_odd = tonumber(ARGV[2])  -- New Pinnacle away odds (decimal, e.g., 1.95)
local draw_odd = tonumber(ARGV[3]) or 0  -- Optional draw odds (for 3-way markets)
local timestamp = ARGV[4]             -- Unix timestamp of update
local market_type = ARGV[5]           -- "moneyline", "puckline", "totals"

-- Step 1: Update Pinnacle odds in Redis (atomic write)
redis.call('HSET', pinnacle_key,
    'home', home_odd,
    'away', away_odd,
    'draw', draw_odd,
    'timestamp', timestamp,
    'market_type', market_type
)

-- Set expiry (30 minutes) to auto-cleanup stale odds
redis.call('EXPIRE', pinnacle_key, 1800)

-- Step 2: Retrieve cached soft book odds
local soft_exists = redis.call('EXISTS', soft_key)

if soft_exists == 0 then
    -- No soft book odds cached yet, can't calculate arb
    return nil
end

local soft_home = tonumber(redis.call('HGET', soft_key, 'home'))
local soft_away = tonumber(redis.call('HGET', soft_key, 'away'))
local soft_draw = tonumber(redis.call('HGET', soft_key, 'draw')) or 0
local soft_timestamp = redis.call('HGET', soft_key, 'timestamp')

-- Validate soft book odds aren't stale (> 60 seconds old)
local current_time = tonumber(timestamp)
local soft_time = tonumber(soft_timestamp)

if (current_time - soft_time) > 60 then
    -- Soft book odds are stale, don't use for arb calculation
    return nil
end

-- Step 3: Calculate arbitrage opportunities
-- Formula: Implied Probability Sum = (1/odd1) + (1/odd2) + ...
-- Arbitrage exists if sum < 1.0 (< 100%)

local arbs = {}  -- Array to store detected arbitrages

-- Scenario A: Pinnacle Home vs Soft Away
if soft_away and soft_away > 0 then
    local prob_a = (1 / home_odd) + (1 / soft_away)
    if prob_a < 1.0 then
        local profit_pct = ((1 / prob_a) - 1) * 100
        table.insert(arbs, {
            type = "2-way",
            leg1 = {book = "pinnacle", market = "home", odd = home_odd},
            leg2 = {book = "soft", market = "away", odd = soft_away},
            profit_pct = string.format("%.2f", profit_pct),
            implied_prob = string.format("%.4f", prob_a)
        })
    end
end

-- Scenario B: Pinnacle Away vs Soft Home
if soft_home and soft_home > 0 then
    local prob_b = (1 / away_odd) + (1 / soft_home)
    if prob_b < 1.0 then
        local profit_pct = ((1 / prob_b) - 1) * 100
        table.insert(arbs, {
            type = "2-way",
            leg1 = {book = "pinnacle", market = "away", odd = away_odd},
            leg2 = {book = "soft", market = "home", odd = soft_home},
            profit_pct = string.format("%.2f", profit_pct),
            implied_prob = string.format("%.4f", prob_b)
        })
    end
end

-- Scenario C: 3-way arbitrage (if draw odds exist)
if draw_odd > 0 and soft_home and soft_away and soft_draw and soft_draw > 0 then
    -- Try all permutations of 3-way arbs
    local permutations = {
        {home_odd, soft_away, soft_draw},  -- Pinny home, Soft away, Soft draw
        {soft_home, away_odd, soft_draw},  -- Soft home, Pinny away, Soft draw
        {soft_home, soft_away, draw_odd},  -- Soft home, Soft away, Pinny draw
    }

    for i, perm in ipairs(permutations) then
        local prob_3way = (1 / perm[1]) + (1 / perm[2]) + (1 / perm[3])
        if prob_3way < 1.0 then
            local profit_pct = ((1 / prob_3way) - 1) * 100
            table.insert(arbs, {
                type = "3-way",
                leg1 = {odd = perm[1]},
                leg2 = {odd = perm[2]},
                leg3 = {odd = perm[3]},
                profit_pct = string.format("%.2f", profit_pct),
                implied_prob = string.format("%.4f", prob_3way)
            })
        end
    end
end

-- Step 4: Return results
if #arbs > 0 then
    -- Encode as JSON-like string (Lua doesn't have native JSON)
    -- Python will parse this
    local result = {
        event_key = string.gsub(pinnacle_key, "odds:pinnacle:", ""),
        market_type = market_type,
        timestamp = timestamp,
        arbitrages = arbs,
        count = #arbs
    }

    -- Simple serialization (Python will parse)
    return cjson.encode(result)
else
    -- No arbitrage found
    return nil
end
