from __future__ import annotations

import logging

from fastapi import FastAPI

from .bot import TradingBot
from .config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)

app = FastAPI(title='Gemini BTC/ETH Bot', version='1.0.0')
bot = TradingBot()


@app.on_event('startup')
def startup() -> None:
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
    }


@app.get('/health')
def health() -> dict:
    return {'status': 'ok', 'settings_loaded': True}


@app.get('/status')
def status() -> dict:
    return bot.last_run


@app.post('/run-now')
def run_now() -> dict:
    return bot.run_cycle()
