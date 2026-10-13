"""Stock, position, and portfolio models with rebalance calculations."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from types import MappingProxyType

ZERO = Decimal("0")
ONE = Decimal("1")
NumericInput = Decimal | int | float | str


def _decimal(value: NumericInput, *, field: str) -> Decimal:
    if isinstance(value, bool):
        raise TypeError(f"{field} must be a number, not a boolean")
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field} must be a finite number") from None
    if not result.is_finite():
        raise ValueError(f"{field} must be a finite number")
    return result


def _ticker(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("ticker must be a non-empty string")
    return value.strip().upper()


@dataclass(frozen=True)
class Stock:
    """A tradable asset identified by its ticker."""

    ticker: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "ticker", _ticker(self.ticker))

    def current_price(self, last_available_price: NumericInput) -> Decimal:
        """Validate and return the quote supplied by the caller."""
        price = _decimal(last_available_price, field=f"price for {self.ticker}")
        if price <= ZERO:
            raise ValueError(f"price for {self.ticker} must be greater than zero")
        return price


@dataclass(frozen=True, init=False)
class Position:
    """A quantity of a stock held in a portfolio."""

    stock: Stock
    shares: Decimal

    def __init__(self, stock: Stock, shares: NumericInput) -> None:
        if not isinstance(stock, Stock):
            raise TypeError("stock must be a Stock instance")
        quantity = _decimal(shares, field=f"shares for {stock.ticker}")
        if quantity < ZERO:
            raise ValueError("shares cannot be negative")
        object.__setattr__(self, "stock", stock)
        object.__setattr__(self, "shares", quantity)

    @property
    def ticker(self) -> str:
        return self.stock.ticker

    def market_value(self, last_available_price: NumericInput) -> Decimal:
        return self.shares * self.stock.current_price(last_available_price)


class TradeSide(str, Enum):
    """Direction of a proposed rebalance order."""

    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True)
class RebalanceOrder:
    """A proposed fractional-share trade."""

    ticker: str
    side: TradeSide
    shares: Decimal
    estimated_value: Decimal
    current_weight: Decimal
    target_weight: Decimal


class Portfolio:
    """Held positions and their target weights, keyed by ticker."""

    def __init__(
        self,
        positions: Iterable[Position],
        allocations: Mapping[str, NumericInput],
    ) -> None:
        positions_by_ticker: dict[str, Position] = {}
        for position in positions:
            if not isinstance(position, Position):
                raise TypeError("positions must contain Position instances")
            if position.ticker in positions_by_ticker:
                raise ValueError(f"duplicate position: {position.ticker}")
            positions_by_ticker[position.ticker] = position

        if not allocations:
            raise ValueError("allocations cannot be empty")

        normalized_allocations: dict[str, Decimal] = {}
        for raw_ticker, raw_weight in allocations.items():
            ticker = _ticker(raw_ticker)
            if ticker in normalized_allocations:
                raise ValueError(f"duplicate allocation for {ticker}")
            weight = _decimal(raw_weight, field=f"allocation for {ticker}")
            if not ZERO <= weight <= ONE:
                raise ValueError(f"allocation for {ticker} must be between 0 and 1")
            normalized_allocations[ticker] = weight

        if sum(normalized_allocations.values(), ZERO) != ONE:
            raise ValueError("allocation weights must sum to exactly 1")

        self.positions = tuple(positions_by_ticker.values())
        self.allocations = MappingProxyType(normalized_allocations)

    def total_value(self, last_available_prices: Mapping[str, NumericInput]) -> Decimal:
        """Return the current market value of the held positions."""
        positions = self._positions_by_ticker()
        prices = self._normalize_prices(last_available_prices)
        self._require_prices(prices, set(positions))
        return sum(
            (
                position.market_value(prices[ticker])
                for ticker, position in positions.items()
            ),
            ZERO,
        )

    def rebalance(
        self, last_available_prices: Mapping[str, NumericInput]
    ) -> list[RebalanceOrder]:
        """Return the fractional-share trades needed to reach target weights."""
        positions = self._positions_by_ticker()
        if not positions:
            return []

        prices = self._normalize_prices(last_available_prices)
        tickers = set(positions) | set(self.allocations)
        self._require_prices(prices, tickers)

        current_values = {
            ticker: position.market_value(prices[ticker])
            for ticker, position in positions.items()
        }
        portfolio_value = sum(current_values.values(), ZERO)
        if portfolio_value == ZERO:
            return []

        current_weights = {
            ticker: value / portfolio_value for ticker, value in current_values.items()
        }
        orders = []
        for ticker in sorted(tickers):
            current_value = current_values.get(ticker, ZERO)
            target_weight = self.allocations.get(ticker, ZERO)
            difference = portfolio_value * target_weight - current_value
            if difference == ZERO:
                continue

            price = prices[ticker]
            shares = abs(difference) / price
            orders.append(
                RebalanceOrder(
                    ticker=ticker,
                    side=TradeSide.BUY if difference > ZERO else TradeSide.SELL,
                    shares=shares,
                    estimated_value=shares * price,
                    current_weight=current_weights.get(ticker, ZERO),
                    target_weight=target_weight,
                )
            )

        return orders

    def _positions_by_ticker(self) -> dict[str, Position]:
        return {position.ticker: position for position in self.positions}

    @staticmethod
    def _normalize_prices(
        last_available_prices: Mapping[str, NumericInput],
    ) -> dict[str, Decimal]:
        prices: dict[str, Decimal] = {}
        for raw_ticker, raw_price in last_available_prices.items():
            ticker = _ticker(raw_ticker)
            if ticker in prices:
                raise ValueError(f"duplicate price quote for {ticker}")
            price = _decimal(raw_price, field=f"price for {ticker}")
            if price <= ZERO:
                raise ValueError(f"price for {ticker} must be greater than zero")
            prices[ticker] = price
        return prices

    @staticmethod
    def _require_prices(prices: Mapping[str, Decimal], tickers: set[str]) -> None:
        missing = sorted(tickers - prices.keys())
        if missing:
            raise ValueError(f"missing price quote(s) for: {', '.join(missing)}")
