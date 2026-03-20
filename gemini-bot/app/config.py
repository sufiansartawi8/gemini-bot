from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_env: str = Field(default='production', alias='APP_ENV')
    log_level: str = Field(default='INFO', alias='LOG_LEVEL')
    dry_run: bool = Field(default=True, alias='DRY_RUN')
    sandbox: bool = Field(default=True, alias='GEMINI_SANDBOX')

    gemini_api_key: str = Field(default='', alias='GEMINI_API_KEY')
    gemini_api_secret: str = Field(default='', alias='GEMINI_API_SECRET')

    symbols: str = Field(default='btcusd,ethusd', alias='SYMBOLS')
    check_interval_seconds: int = Field(default=300, alias='CHECK_INTERVAL_SECONDS')
    candle_interval: str = Field(default='15m', alias='CANDLE_INTERVAL')
    lookback_candles: int = Field(default=120, alias='LOOKBACK_CANDLES')

    max_notional_per_symbol_usd: float = Field(default=500.0, alias='MAX_NOTIONAL_PER_SYMBOL_USD')
    reserve_cash_usd: float = Field(default=25.0, alias='RESERVE_CASH_USD')
    max_open_positions: int = Field(default=2, alias='MAX_OPEN_POSITIONS')
    stop_loss_pct: float = Field(default=0.025, alias='STOP_LOSS_PCT')
    take_profit_pct: float = Field(default=0.05, alias='TAKE_PROFIT_PCT')
    max_slippage_bps: int = Field(default=15, alias='MAX_SLIPPAGE_BPS')
    maker_or_cancel: bool = Field(default=False, alias='MAKER_OR_CANCEL')

    fast_ema: int = Field(default=9, alias='FAST_EMA')
    slow_ema: int = Field(default=21, alias='SLOW_EMA')
    rsi_period: int = Field(default=14, alias='RSI_PERIOD')
    rsi_buy_max: float = Field(default=68.0, alias='RSI_BUY_MAX')
    rsi_sell_min: float = Field(default=42.0, alias='RSI_SELL_MIN')

    webhook_url: str = Field(default='', alias='WEBHOOK_URL')
    port: int = Field(default=8000, alias='PORT')

    @property
    def parsed_symbols(self) -> list[str]:
        return [s.strip().lower() for s in self.symbols.split(',') if s.strip()]

    @property
    def base_url(self) -> str:
        return 'https://api.sandbox.gemini.com' if self.sandbox else 'https://api.gemini.com'


settings = Settings()
