from __future__ import annotations

import logging

from fastapi import FastAPI

from .bot import TradingBot
from .config import settings
from .gemini_client import GeminiAPIError, GeminiClient

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)

app = FastAPI(title='Gemini BTC/ETH Bot', version='1.1.0')
bot = TradingBot()
client = GeminiClient()


@app.on_event('startup')
def startup() -> None:
    if settings.auto_start_bot:
        bot.start()


@app.on_event('shutdown')
def shutdown() -> None:
    bot.stop()


@app.get('/')
def root() -> dict:
    return {
        'name': 'gemini-btc-eth-bot',
        'dry_run': settings.dry_run,
        'sandbox': settings.sandbox,
        'symbols': settings.parsed_symbols,
        'auto_start_bot': settings.auto_start_bot,
        'private_api_ready': settings.private_api_ready,
    }


@app.get('/health')
def health() -> dict:
    return {'status': 'ok', 'settings_loaded': True}


@app.get('/status')
def status() -> dict:
    return bot.last_run


@app.get('/config')
def config() -> dict:
    return {
        'dry_run': settings.dry_run,
        'sandbox': settings.sandbox,
        'auto_start_bot': settings.auto_start_bot,
        'enable_private_api': settings.enable_private_api,
        'private_api_ready': settings.private_api_ready,
        'symbols': settings.parsed_symbols,
        'check_interval_seconds': settings.check_interval_seconds,
        'candle_interval': settings.candle_interval,
        'lookback_candles': settings.lookback_candles,
        'max_notional_per_symbol_usd': settings.max_notional_per_symbol_usd,
    }


@app.get('/auth-check')
def auth_check() -> dict:
    if not settings.private_api_ready:
        return {'ok': False, 'message': 'Private Gemini API is disabled or credentials are missing.'}
    try:
        return client.auth_check()
    except GeminiAPIError as exc:
        return {'ok': False, 'message': str(exc)}


@app.post('/start')
def start() -> dict:
    bot.start()
    return {'status': 'started', 'interval_seconds': settings.check_interval_seconds}


@app.post('/stop')
def stop() -> dict:
    bot.stop()
    return {'status': 'stopped'}


@app.post('/run-now')
def run_now() -> dict:
    return bot.run_cycle()
