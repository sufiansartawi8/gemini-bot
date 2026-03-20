from __future__ import annotations

import json
import logging
import threading
import time
from collections import defaultdict
from typing import Any

import httpx

from .config import settings
from .gemini_client import GeminiClient
from .schemas import Decision, Position
from .strategy import EmaRsiStrategy

logger = logging.getLogger(__name__)


class TradingBot:
    def __init__(self) -> None:
        self.client = GeminiClient()
        self.strategy = EmaRsiStrategy()
        self.running = False
        self.thread: threading.Thread | None = None
        self.last_run: dict[str, Any] = {'status': 'idle', 'decisions': []}

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

    def _run_loop(self) -> None:
        while self.running:
            try:
                self.run_cycle()
            except Exception as exc:
                logger.exception('cycle failed: %s', exc)
                self.last_run = {'status': 'error', 'error': str(exc), 'decisions': []}
            time.sleep(settings.check_interval_seconds)

    def run_cycle(self) -> dict[str, Any]:
        balances = self.client.get_balances() if not settings.dry_run or settings.gemini_api_key else []
        positions = self._positions_from_balances(balances)

        decisions: list[dict[str, Any]] = []
        open_positions = sum(1 for p in positions.values() if p.amount > 0)

        for symbol in settings.parsed_symbols:
            candles = self.client.get_candles(symbol, settings.candle_interval)
            if len(candles) < max(settings.slow_ema + 2, settings.rsi_period + 2):
                decisions.append({'symbol': symbol, 'action': 'hold', 'reason': 'not enough candles'})
                continue

            ticker = self.client.get_ticker(symbol)
            last_price = float(ticker['last'])
            position = positions.get(symbol, Position(symbol=symbol, amount=0.0, avg_price=0.0, last_price=last_price))
            position.last_price = last_price
            decision = self.strategy.evaluate(symbol, candles, position)

            if decision.action == 'buy' and open_positions >= settings.max_open_positions:
                decision = Decision('hold', symbol, 'max open positions reached', last_price)

            executed = None
            if decision.action == 'buy':
                amount = self._size_buy(symbol, last_price, balances)
                if amount > 0:
                    decision.amount = amount
                    executed = self._execute(decision)
                    if executed is not None:
                        open_positions += 1
                else:
                    decision = Decision('hold', symbol, 'insufficient USD for new position', last_price)
            elif decision.action == 'sell' and position.amount > 0:
                decision.amount = position.amount
                executed = self._execute(decision)

            decisions.append(
                {
                    'symbol': symbol,
                    'action': decision.action,
                    'reason': decision.reason,
                    'price': round(decision.price, 4),
                    'amount': round(decision.amount, 8),
                    'executed': executed,
                }
            )

        self.last_run = {'status': 'ok', 'decisions': decisions, 'ts': int(time.time())}
        logger.info('cycle complete: %s', json.dumps(self.last_run))
        if settings.webhook_url:
            self._notify(self.last_run)
        return self.last_run

    def _execute(self, decision: Decision) -> dict[str, Any] | None:
        price = decision.price
        slippage = 1 + (settings.max_slippage_bps / 10_000)
        order_price = price * slippage if decision.action == 'buy' else price * (1 - (settings.max_slippage_bps / 10_000))

        if settings.dry_run:
            logger.info('DRY RUN %s %s amount=%s at %s', decision.action, decision.symbol, decision.amount, order_price)
            return {
                'mode': 'dry_run',
                'side': decision.action,
                'symbol': decision.symbol,
                'amount': decision.amount,
                'price': round(order_price, 2),
            }

        order = self.client.place_limit_order(
            symbol=decision.symbol,
            side=decision.action,
            amount=decision.amount,
            price=order_price,
        )
        logger.info('live order: %s', order)
        return order

    def _positions_from_balances(self, balances: list[dict[str, Any]]) -> dict[str, Position]:
        out: dict[str, Position] = {}
        avg_prices = self._estimate_entry_prices()
        for symbol in settings.parsed_symbols:
            asset = symbol.replace('usd', '').upper()
            bal = next((b for b in balances if b.get('currency') == asset), None)
            amount = float(bal.get('available', 0) if bal else 0)
            out[symbol] = Position(symbol=symbol, amount=amount, avg_price=avg_prices.get(symbol, 0.0))
        return out

    def _estimate_entry_prices(self) -> dict[str, float]:
        prices: dict[str, float] = {}
        for symbol in settings.parsed_symbols:
            try:
                trades = self.client.get_trades(symbol, limit_trades=50) if settings.gemini_api_key and not settings.dry_run else []
            except Exception:
                trades = []
            buys = [t for t in trades if t.get('type') == 'Buy' or t.get('side') == 'buy']
            if not buys:
                prices[symbol] = 0.0
                continue
            total_qty = sum(float(t.get('amount', t.get('fee_amount', 0) or 0)) for t in buys if float(t.get('amount', 0) or 0) > 0)
            total_cost = sum(float(t.get('amount', 0) or 0) * float(t.get('price', 0) or 0) for t in buys)
            prices[symbol] = (total_cost / total_qty) if total_qty else 0.0
        return prices

    def _size_buy(self, symbol: str, last_price: float, balances: list[dict[str, Any]]) -> float:
        usd_bal = next((b for b in balances if b.get('currency') == 'USD'), None)
        available_usd = float(usd_bal.get('available', 0) if usd_bal else settings.max_notional_per_symbol_usd)
        spend = min(settings.max_notional_per_symbol_usd, max(0.0, available_usd - settings.reserve_cash_usd))
        if spend <= 10:
            return 0.0
        return spend / last_price

    def _notify(self, payload: dict[str, Any]) -> None:
        try:
            httpx.post(settings.webhook_url, json=payload, timeout=10)
        except Exception:
            logger.exception('webhook failed')
