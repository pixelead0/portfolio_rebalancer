"""Tests for the manual browser helper's display formatting."""

import unittest

from tools.manual_web import calculate


class ManualWebTests(unittest.TestCase):
    def test_shares_and_weights_are_rounded_to_two_decimal_places(self):
        result = calculate(
            {
                "positions": [
                    {
                        "ticker": "aapl",
                        "shares": "10",
                        "price": "20",
                        "target_percent": "90",
                    },
                    {
                        "ticker": "mas",
                        "shares": "1",
                        "price": "20",
                        "target_percent": "10",
                    },
                ]
            }
        )
        orders = {order["ticker"]: order for order in result["orders"]}

        self.assertEqual(orders["AAPL"]["shares"], "0.10")
        self.assertEqual(orders["MAS"]["shares"], "0.10")
        self.assertEqual(orders["AAPL"]["current_weight_percent"], "90.91")
        self.assertEqual(orders["AAPL"]["target_weight_percent"], "90.00")
        self.assertEqual(orders["MAS"]["current_weight_percent"], "9.09")
        self.assertEqual(orders["MAS"]["target_weight_percent"], "10.00")


if __name__ == "__main__":
    unittest.main()
