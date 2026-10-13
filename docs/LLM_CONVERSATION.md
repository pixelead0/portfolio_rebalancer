# Prompt Development Record

This document shows how the request was refined into the implementation. The prompt drafts below are reconstructed and edited for clarity; they are not verbatim chat excerpts. Include the original conversation link or export when submitting, as the exercise requests the conversation itself.

## 1. Starting point: solve the assignment

**Initial prompt, condensed from the take-home:**

> Build a simple Python `Portfolio` containing stocks and target allocations. Given each stock's latest available price, return the stocks and quantities to buy or sell to reach the target allocation. Explain the design.

This establishes the core calculation, but leaves the boundaries between an asset, a holding, and a price source open.

## 2. Refine the model and API

**Refined prompt:**

> Keep the design small. A `Stock` represents an asset identified by ticker; the quantity held belongs to a portfolio position. Model `Position(stock, shares)` separately. Let `Stock.current_price(last_available_price)` validate and return the price supplied by the caller. Make `Portfolio.rebalance(prices)` return proposed trades only; do not fetch quotes or execute orders. Support fractional shares and use `Decimal` for all financial calculations.

This led to three domain concepts: `Stock`, `Position`, and `Portfolio`. Prices are explicit inputs rather than hidden mutable state or an external service.

## 3. Specify the rebalance and edge cases

**Calculation prompt:**

> Value the current positions using the supplied prices. For each ticker, compare its current value with its target share of the portfolio's current invested value. Return a buy for a deficit or a sell for an excess, with the fractional quantity derived from the supplied price. Treat a held ticker missing from the target as a zero-weight position, and a target ticker not currently held as having zero current value.

For current value `V` and target weight `w`, the target value is `V * w`. The signed difference between target value and current value determines the trade side; its absolute value divided by the current price determines the shares. Target weights must sum exactly to `1`. Prices must be positive and quantities non-negative.

Cash, fees, taxes, short selling, and whole-share restrictions remain out of scope because the assignment does not define their behavior.

## 4. Review for scope and simplicity

A review pass challenged two unnecessary choices: treating the share quantity as part of `Stock`, and presenting a browser UI as part of the take-home solution. The model was kept as `Stock` plus `Position`; unnecessary README explanation was removed. The core deliverable stayed focused on the portfolio calculation and tests.

## 5. Add a separate manual-testing interface

This was a follow-up request, not a requirement of the take-home.

**Follow-up prompt:**

> Add a local browser interface only for manual testing. Let me enter positions, prices, and target percentages in an editable table, then show the proposed rebalance. Keep it outside the core package and do not add runtime dependencies.

The helper is implemented in `tools/manual_web.py` and `tools/manual_web.html`. It uses the same portfolio calculation, makes no external price requests, and is excluded from the built package. The table layout was retained after review in preference to a text-entry form.

During manual testing, the browser showed an old server response without the weight fields; checking the POST response revealed that the running process had not loaded the updated code. After verifying the current endpoint, presentation feedback led to formatting proposed share quantities and current/target weights to two decimal places. This affects display only; `Decimal` calculations retain their full precision.

## Validation

- `make check`: formatting, lint, and all 16 unit tests pass.
- The manual interface's GET page and POST rebalance endpoint were smoke-tested with buy and sell examples.
- `make build` succeeds; the wheel does not contain the manual-testing helper.
