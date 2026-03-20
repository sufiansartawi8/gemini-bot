from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from decimal import Decimal, ROUND_DOWN
from typing import Any

import httpx

from .config import settings
from .schemas import Candle


class GeminiClient:
    def __init__(self) -> None:
        self.base_url = settings.base_url
        self.api_key = settings.gemini_api_key
        self.api_secret = settings.gemini_api_secret.encode() if settings.gemini_api_secret else b''
        self.client = httpx.Client(timeout=20)

    def _nonce(self) -> int:
        return int(time.time())

    def _headers(self, payload: dict[str, Any]) -> dict[str, str]:
        encoded = base64.b64encode(json.dumps(payload).encode())
        signature = hmac.new(self.api_secret, encoded, hashlib.sha384).hexdigest()
        return {
            'Content-Type': 'text/plain',
            'Content-Length': '0',
            'Cache-Control': 'no-cache',
            'X-GEMINI-APIKEY': self.api_key,
            'X-GEMINI-PAYLOAD': encoded.decode(),
            'X-GEMINI-SIGNATURE': signature,
        }

    def _private_post(self, path: str, extra: dict[str, Any] | None = None) -> Any:
        payload = {'request': path, 'nonce': self._nonce()}
        if extra:
            payload.update(extra)
        response = self.client.post(f'{self.base_url}{path}', headers=self._headers(payload))
        response.raise_for_status()
        return response.json()

    def health(self) -> dict[str, Any]:
        resp = self.client.get(f'{self.base_url}/v1/symbols')
        resp.raise_for_status()
        return {'ok': True, 'sandbox': settings.sandbox}

    def get_ticker(self, symbol: str) -> dict[str, Any]:
        resp = self.client.get(f'{self.base_url}/v1/pubticker/{symbol}')
        resp.raise_for_status()
        return resp.json()

    def get_candles(self, symbol: str, interval: str = '15m') -> list[Candle]:
        resp = self.client.get(f'{self.base_url}/v2/candles/{symbol}/{interval}')
        resp.raise_for_status()
        rows = resp.json()
        rows.reverse()  # oldest -> newest
        return [
            Candle(
                timestamp_ms=int(r[0]),
                open=float(r[1]),
                high=float(r[2]),
                low=float(r[3]),
                close=float(r[4]),
                volume=float(r[5]),
            )
            for r in rows[-settings.lookback_candles :]
        ]

    def get_balances(self) -> list[dict[str, Any]]:
        return self._private_post('/v1/balances', {'showPendingBalances': False})

    def get_active_orders(self) -> list[dict[str, Any]]:
        return self._private_post('/v1/orders')

    def get_trades(self, symbol: str, limit_trades: int = 50) -> list[dict[str, Any]]:
        return self._private_post('/v1/mytrades', {'symbol': symbol, 'limit_trades': limit_trades})

    def cancel_all_session_orders(self) -> Any:
        return self._private_post('/v1/order/cancel/session')

    def heartbeat(self) -> Any:
        return self._private_post('/v1/heartbeat')

    def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Any:
        options = ['maker-or-cancel'] if settings.maker_or_cancel else []
        payload = {
            'symbol': symbol,
            'amount': self._fmt_amount(amount),
            'price': self._fmt_price(price),
            'side': side,
            'type': 'exchange limit',
            'options': options,
        }
        return self._private_post('/v1/order/new', payload)

    @staticmethod
    def _fmt_price(value: float) -> str:
        return str(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_DOWN))

    @staticmethod
    def _fmt_amount(value: float) -> str:
        return format(Decimal(str(value)).quantize(Decimal('0.00000001'), rounding=ROUND_DOWN), 'f')
