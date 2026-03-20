from __future__ import annotations

from .config import settings
from .indicators import ema, rsi
from .schemas import Candle, Decision, Position


class EmaRsiStrategy:
    def evaluate(self, symbol: str, candles: list[Candle], position: Position | None) -> Decision:
        closes = [c.close for c in candles]
        price = closes[-1]
        fast = ema(closes, settings.fast_ema)
        slow = ema(closes, settings.slow_ema)
        rsi_series = rsi(closes, settings.rsi_period)

        fast_now, fast_prev = fast[-1], fast[-2]
        slow_now, slow_prev = slow[-1], slow[-2]
        rsi_now = rsi_series[-1]

        bullish_cross = fast_prev <= slow_prev and fast_now > slow_now
        bearish_cross = fast_prev >= slow_prev and fast_now < slow_now

        if position and position.amount > 0:
            entry = position.avg_price or price
            pnl_pct = (price - entry) / entry if entry else 0.0
            if pnl_pct <= -settings.stop_loss_pct:
                return Decision('sell', symbol, f'stop loss hit ({pnl_pct:.2%})', price)
            if pnl_pct >= settings.take_profit_pct:
                return Decision('sell', symbol, f'take profit hit ({pnl_pct:.2%})', price)
            if bearish_cross or rsi_now < settings.rsi_sell_min:
                return Decision('sell', symbol, f'bearish exit: cross={bearish_cross}, rsi={rsi_now:.1f}', price)
            return Decision('hold', symbol, f'position held: rsi={rsi_now:.1f}', price)

        if bullish_cross and rsi_now < settings.rsi_buy_max:
            return Decision('buy', symbol, f'bullish entry: cross={bullish_cross}, rsi={rsi_now:.1f}', price)

        return Decision('hold', symbol, f'no setup: cross={bullish_cross}, rsi={rsi_now:.1f}', price)
