# Gemini BTC/ETH bot

A small Python bot for BTC/USD and ETH/USD on Gemini, designed for GitHub + Railway deployment.

## What changed in this version
- no forced trading loop on startup by default
- safer Railway deployment with `AUTO_START_BOT=false`
- better Gemini private-auth handling and clearer error messages
- `GET /auth-check` endpoint to verify Gemini credentials
- dry-run mode works even with no private keys configured
- richer signal metadata in `/status` and `/run-now`

## Recommended Railway variables
Use these exact names:

```env
APP_ENV=production
LOG_LEVEL=INFO
DRY_RUN=true
GEMINI_SANDBOX=true
AUTO_START_BOT=false
ENABLE_PRIVATE_API=false

GEMINI_API_KEY=
GEMINI_API_SECRET=

SYMBOLS=btcusd,ethusd
CHECK_INTERVAL_SECONDS=900
CANDLE_INTERVAL=15m
LOOKBACK_CANDLES=180

MAX_NOTIONAL_PER_SYMBOL_USD=500
RESERVE_CASH_USD=25
MAX_OPEN_POSITIONS=2
STOP_LOSS_PCT=0.025
TAKE_PROFIT_PCT=0.05
MAX_SLIPPAGE_BPS=15
MAKER_OR_CANCEL=false

FAST_EMA=9
SLOW_EMA=21
RSI_PERIOD=14
RSI_BUY_MAX=68
RSI_SELL_MIN=42

WEBHOOK_URL=
```

## Safe startup flow
1. Deploy with:
   - `DRY_RUN=true`
   - `GEMINI_SANDBOX=true`
   - `ENABLE_PRIVATE_API=false`
   - `AUTO_START_BOT=false`
2. Open `/health`
3. Open `/config`
4. Run `POST /run-now`
5. When ready to test Gemini credentials, add the key/secret and set:
   - `ENABLE_PRIVATE_API=true`
6. Open `/auth-check`

## Endpoints
- `GET /health`
- `GET /config`
- `GET /status`
- `GET /auth-check`
- `POST /run-now`
- `POST /start`
- `POST /stop`

## Notes
- With `ENABLE_PRIVATE_API=false`, the bot uses public Gemini market data only.
- With `DRY_RUN=true`, no live orders are submitted.
- With `AUTO_START_BOT=false`, Railway will stay stable and wait for manual runs.
- To enable live trading, set both `ENABLE_PRIVATE_API=true` and `DRY_RUN=false`, then verify `/auth-check` first.
