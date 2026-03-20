# Gemini BTC/ETH bot

A small Python bot that trades `btcusd` and `ethusd` on Gemini, runs on Railway, and is safe to start in **sandbox + dry-run** mode first.

## What it does
- Pulls Gemini candles and ticker data
- Uses a simple **EMA crossover + RSI filter** strategy
- Caps budget to **$500 per symbol** by default
- Exits on bearish signal, stop-loss, or take-profit
- Exposes `/health`, `/status`, and `/run-now`
- Deploys cleanly to Railway from GitHub

## Strategy
Entry:
- fast EMA crosses above slow EMA
- RSI is below the buy ceiling

Exit:
- bearish EMA cross
- RSI weakens below sell threshold
- stop-loss or take-profit gets hit

This is intentionally conservative and easy to inspect. It is **not** guaranteed to be profitable.

## Gemini API key setup
Create a Gemini API key with:
- **Trader** role
- **Uses a time-based nonce** enabled
- Start with **sandbox** first

Gemini requires a nonce on every private request, and time-based nonces must be within ±30 seconds of Unix time. Gemini private endpoints are authenticated with `X-GEMINI-APIKEY`, `X-GEMINI-PAYLOAD`, and `X-GEMINI-SIGNATURE`, where the payload is base64 JSON and the signature is HMAC-SHA384. The Trader role can check balances and place/cancel orders. citeturn758936view1turn692002search2

## Railway deployment
Railway can deploy a FastAPI app directly from a GitHub repo or from a Dockerfile, and a `railway.json` file can define deployment behavior like a healthcheck path. Environment variables are available at runtime through Railway Variables. citeturn758936view3turn163532search1turn163532search5

### 1) Push to GitHub
```bash
git init
git add .
git commit -m "Initial Gemini BTC/ETH bot"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/gemini-btc-eth-bot.git
git push -u origin main
```

### 2) Deploy to Railway
- New Project
- Deploy from GitHub repo
- Select this repo
- Add the variables from `.env.example`
- Generate a public domain

### 3) Start safely
Use these first:
```env
DRY_RUN=true
GEMINI_SANDBOX=true
```
Then hit:
- `GET /status`
- `POST /run-now`

Only flip to live after you verify several dry-run cycles.

## Notes on symbols and sizing
Gemini documents symbol precision and minimum order constraints, and BTC/USD and ETH/USD are supported live symbols. Quantity and price on incoming orders must respect Gemini minimums and increments. citeturn758936view2turn903576search3

The bot sizes entries as:
- spend = min(available USD minus reserve, $500)
- amount = spend / last price

## Suggested repo structure
```text
app/
  bot.py
  config.py
  gemini_client.py
  indicators.py
  main.py
  schemas.py
  strategy.py
.env.example
Dockerfile
railway.json
requirements.txt
README.md
```

## Good next upgrades
- use Gemini WebSocket order events instead of polling for order state
- add ATR-based position sizing
- store trades and performance in Postgres
- add CoinGecko/news/sentiment filters behind feature flags
- add backtesting notebook before live trading

## Warning
This is real trading automation. Crypto is volatile, fees and slippage matter, and a simple rules strategy can lose money in choppy conditions. Test in sandbox and dry-run first.
