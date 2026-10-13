"""Local browser helper for manually checking rebalance proposals."""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from portfolio_rebalancer import Portfolio, Position, Stock

HUNDRED = Decimal("100")
MAX_REQUEST_BYTES = 64_000


def _decimal_text(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _two_decimal_text(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")


def calculate(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or not isinstance(payload.get("positions"), list):
        raise ValueError("Enter portfolio positions to calculate a rebalance.")

    rows = payload["positions"]
    if not rows:
        raise ValueError("Enter at least one position.")

    positions = []
    allocations: dict[str, Decimal] = {}
    prices: dict[str, Any] = {}
    percentage_total = Decimal("0")

    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Each position must be a row of values.")

        ticker = row.get("ticker")
        if not isinstance(ticker, str) or not ticker.strip():
            raise ValueError("Every position needs a ticker.")
        ticker = ticker.strip().upper()

        try:
            percentage = Decimal(str(row.get("target_percent", "")))
        except (InvalidOperation, ValueError):
            raise ValueError(f"Enter a valid target percentage for {ticker}.") from None
        if not percentage.is_finite() or not Decimal("0") <= percentage <= HUNDRED:
            raise ValueError(f"The target for {ticker} must be between 0 and 100%.")

        positions.append(Position(Stock(ticker), row.get("shares")))
        allocations[ticker] = percentage / HUNDRED
        prices[ticker] = row.get("price")
        percentage_total += percentage

    if percentage_total != HUNDRED:
        raise ValueError("Target percentages must sum exactly to 100%.")

    portfolio = Portfolio(positions, allocations)
    orders = portfolio.rebalance(prices)
    return {
        "portfolio_value": _decimal_text(portfolio.total_value(prices)),
        "orders": [
            {
                "ticker": order.ticker,
                "side": order.side.value,
                "shares": _two_decimal_text(order.shares),
                "estimated_value": _decimal_text(order.estimated_value),
                "current_weight_percent": _two_decimal_text(
                    order.current_weight * HUNDRED
                ),
                "target_weight_percent": _two_decimal_text(
                    order.target_weight * HUNDRED
                ),
            }
            for order in orders
        ],
    }


class ManualWebHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/":
            self.send_error(404)
            return
        page = Path(__file__).with_name("manual_web.html").read_bytes()
        self._send(200, page, "text/html; charset=utf-8")

    def do_POST(self) -> None:
        if self.path != "/rebalance":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise ValueError("Request size is invalid.")
            result = calculate(json.loads(self.rfile.read(length)))
        except (json.JSONDecodeError, InvalidOperation, TypeError, ValueError) as error:
            self._send(
                400, json.dumps({"error": str(error)}).encode(), "application/json"
            )
            return

        self._send(200, json.dumps(result).encode(), "application/json")

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = HTTPServer(("127.0.0.1", 8000), ManualWebHandler)
    print("Manual test UI: http://127.0.0.1:8000 (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
