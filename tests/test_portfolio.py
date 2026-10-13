"""Unit tests for stock, position, and portfolio calculations."""

import unittest
from decimal import Decimal

from portfolio_rebalancer import Portfolio, Position, Stock, TradeSide


class StockTests(unittest.TestCase):
    def test_current_price_returns_the_supplied_quote(self):
        stock = Stock("meta")

        self.assertEqual(stock.ticker, "META")
        self.assertEqual(stock.current_price("123.45"), Decimal("123.45"))

    def test_rejects_non_positive_price(self):
        with self.assertRaisesRegex(ValueError, "must be greater than zero"):
            Stock("META").current_price(0)


class PositionTests(unittest.TestCase):
    def test_market_value_uses_position_quantity_and_stock_price(self):
        position = Position(Stock("META"), "2.5")

        self.assertEqual(position.market_value("123.45"), Decimal("308.625"))

    def test_rejects_negative_share_quantity(self):
        with self.assertRaisesRegex(ValueError, "shares cannot be negative"):
            Position(Stock("META"), -1)


class PortfolioTests(unittest.TestCase):
    def setUp(self):
        self.portfolio = Portfolio(
            positions=[
                Position(Stock("META"), 2),
                Position(Stock("AAPL"), 10),
            ],
            allocations={"META": "0.4", "AAPL": "0.6"},
        )

    def test_total_value_uses_supplied_prices(self):
        self.assertEqual(
            self.portfolio.total_value({"META": 100, "AAPL": 20}),
            Decimal("400"),
        )

    def test_rebalance_returns_fractional_sell_and_buy_orders(self):
        orders = self.portfolio.rebalance({"META": 100, "AAPL": 20})

        self.assertEqual([order.ticker for order in orders], ["AAPL", "META"])
        aapl_order, meta_order = orders
        self.assertEqual(aapl_order.side, TradeSide.BUY)
        self.assertEqual(aapl_order.shares, Decimal("2"))
        self.assertEqual(aapl_order.estimated_value, Decimal("40"))
        self.assertEqual(aapl_order.current_weight, Decimal("0.5"))
        self.assertEqual(aapl_order.target_weight, Decimal("0.6"))
        self.assertEqual(meta_order.side, TradeSide.SELL)
        self.assertEqual(meta_order.shares, Decimal("0.4"))
        self.assertEqual(meta_order.estimated_value, Decimal("40.0"))
        self.assertEqual(meta_order.current_weight, Decimal("0.5"))
        self.assertEqual(meta_order.target_weight, Decimal("0.4"))

    def test_buys_a_target_asset_not_currently_held(self):
        portfolio = Portfolio(
            positions=[Position(Stock("META"), 2)],
            allocations={"META": "0.5", "AAPL": "0.5"},
        )

        orders = portfolio.rebalance({"META": 100, "AAPL": 25})

        aapl_order = next(order for order in orders if order.ticker == "AAPL")
        self.assertEqual(aapl_order.side, TradeSide.BUY)
        self.assertEqual(aapl_order.shares, Decimal("4"))
        self.assertEqual(aapl_order.estimated_value, Decimal("100"))

    def test_sells_a_position_missing_from_target_allocations(self):
        portfolio = Portfolio(
            positions=[Position(Stock("META"), 1), Position(Stock("TSLA"), 2)],
            allocations={"META": 1},
        )

        orders = portfolio.rebalance({"META": 100, "TSLA": 50})

        meta_order, tsla_order = orders
        self.assertEqual(meta_order.side, TradeSide.BUY)
        self.assertEqual(meta_order.shares, Decimal("1"))
        self.assertEqual(tsla_order.side, TradeSide.SELL)
        self.assertEqual(tsla_order.shares, Decimal("2"))
        self.assertEqual(tsla_order.target_weight, Decimal("0"))

    def test_balanced_portfolio_has_no_orders(self):
        portfolio = Portfolio(
            positions=[
                Position(Stock("META"), 4),
                Position(Stock("AAPL"), 6),
            ],
            allocations={"META": "0.4", "AAPL": "0.6"},
        )

        self.assertEqual(portfolio.rebalance({"META": 100, "AAPL": 100}), [])

    def test_empty_portfolio_has_no_orders(self):
        portfolio = Portfolio([], {"META": "0.4", "AAPL": "0.6"})

        self.assertEqual(portfolio.rebalance({}), [])

    def test_zero_value_positions_have_no_orders(self):
        portfolio = Portfolio(
            [Position(Stock("META"), 0)],
            {"META": 1},
        )

        self.assertEqual(portfolio.rebalance({"META": 100}), [])

    def test_rejects_allocations_that_do_not_sum_to_one(self):
        with self.assertRaisesRegex(ValueError, "sum to exactly 1"):
            Portfolio([], {"META": "0.4", "AAPL": "0.5"})

    def test_rejects_missing_price_quote(self):
        with self.assertRaisesRegex(ValueError, "missing price quote.*AAPL"):
            self.portfolio.rebalance({"META": 100})

    def test_rejects_duplicate_positions_case_insensitively(self):
        positions = [Position(Stock("META"), 1), Position(Stock("meta"), 2)]

        with self.assertRaisesRegex(ValueError, "duplicate position: META"):
            Portfolio(positions, {"META": 1})

    def test_accepts_fractional_position_quantity(self):
        portfolio = Portfolio(
            positions=[Position(Stock("META"), "1.25")],
            allocations={"META": 1},
        )

        self.assertEqual(portfolio.total_value({"META": 80}), Decimal("100.00"))
        self.assertEqual(portfolio.rebalance({"META": 80}), [])


if __name__ == "__main__":
    unittest.main()
