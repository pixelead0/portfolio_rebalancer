# Portfolio Rebalancer

Python module for calculating portfolio rebalance orders with fractional shares.

## Design

- `Stock` represents an asset by ticker. `Stock.current_price(last_available_price)` validates and returns the quote supplied by the caller.
- `Position` associates a stock with the quantity held.
- `Portfolio` stores positions and target weights. `rebalance(prices)` returns proposed trades; it does not execute them.
- Prices, quantities, weights, and calculations use `Decimal`.
- Target weights are fractions that must sum exactly to `1`. Prices must be positive and use the same currency.
- Positions omitted from the target allocation have a target weight of zero. Target assets not currently held can be bought.
- Cash, fees, taxes, short selling, and whole-share restrictions are not modeled.

## Install and test

```bash
make sync
make check
```

`make test` runs the unit tests. `make format-check` and `make lint` run the individual style checks. GitHub Actions runs these checks on pushes and pull requests to `main`, across Python 3.10–3.13, and builds the distribution.

## Versioning and releases

The version in `pyproject.toml` is the source of truth. To prepare a release:

1. Update the project version using [Semantic Versioning](https://semver.org/).
2. Run `uv lock` to refresh the lockfile, then run `make check` and `make build`.
3. Commit and merge the version change to `main`.
4. Create and push a matching tag, for example:

   ```bash
   git tag -a v0.2.0 -m "Release v0.2.0"
   git push origin v0.2.0
   ```

The release workflow reruns validation, confirms the tag matches `pyproject.toml`, builds the source distribution and wheel, and attaches them to a GitHub Release. It does not publish to PyPI.

## Manual test UI

Run `make manual-ui` and open [http://127.0.0.1:8000](http://127.0.0.1:8000). Add a row for each asset, enter its shares, latest price, and target percentage, then select **Calcular / recalcular**. Keep the terminal open while testing and stop the server with `Ctrl+C`.

This helper lives in `tools/` and exists only for manual checks. It is not part of the portfolio package or its build; prices remain caller-supplied, and no trades are executed.

## Example

The portfolio below is worth $400: $200 in META and $200 in AAPL. The target is 40% META and 60% AAPL.

```python
from decimal import Decimal

from portfolio_rebalancer import Portfolio, Position, Stock

portfolio = Portfolio(
    positions=[
        Position(Stock("META"), Decimal("2")),
        Position(Stock("AAPL"), Decimal("10")),
    ],
    allocations={"META": Decimal("0.40"), "AAPL": Decimal("0.60")},
)

prices = {"META": Decimal("100"), "AAPL": Decimal("20")}
orders = portfolio.rebalance(prices)

for order in orders:
    print(
        f"{order.side.value.upper()}: {order.shares} {order.ticker} "
        f"(about ${order.estimated_value:.2f})"
    )
```

Output:

```text
BUY: 2 AAPL (about $40.00)
SELL: 0.4 META (about $40.00)
```

## Project layout

```text
src/portfolio_rebalancer/  # Domain model
 tests/                    # Unit tests
 tools/                    # Manual-only test helper
 docs/                     # LLM conversation record
 .agents/                  # Agent guidance
```

[`docs/LLM_CONVERSATION.md`](docs/LLM_CONVERSATION.md) summarizes how the initial prompt evolved through clarifications, design constraints, and review feedback. Include the original conversation link or export when submitting, as required by the exercise.
