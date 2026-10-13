# Portfolio Rebalancing Domain

## Model

- `Stock` represents an asset identified by ticker.
- `Position` represents the quantity of a `Stock` held by a portfolio.
- `Stock.current_price(last_available_price)` validates and returns the caller-supplied quote; it does not contact an external provider.
- `Portfolio.allocations` contains target weights as decimal fractions. They must sum exactly to `1`.
- `Portfolio.rebalance(prices)` compares current market values with target values based on the current invested portfolio value.
- Orders may use fractional shares. Positions omitted from the target allocation have a target weight of zero.

## Invariants and Scope

- Use `Decimal` for all financial domain calculations.
- Validate strictly positive prices, non-negative quantities, non-empty tickers, and required quotes for held and target assets.
- Return a deterministic, sorted list of proposals; do not mutate holdings or execute trades.
- Do not model initial cash, fees, taxes, lot-size restrictions, short selling, or price providers unless the scope is explicitly changed.
- An empty portfolio has no value basis to distribute and currently returns an empty order list.
- Keep tests for balanced portfolios, buys, sells, fractional quantities, target assets not currently held, positions omitted from the target allocation, and invalid inputs.
