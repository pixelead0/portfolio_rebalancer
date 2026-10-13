# Agent Instructions

## Repository Goal

This repository contains a self-contained Python solution to Fintual's portfolio rebalancing exercise. The domain API lives in `src/portfolio_rebalancer/`; tests are in `tests/`.

## Working Rules

- Read `.agents/instructions/portfolio-domain.md` before changing financial logic.
- Keep the solution free of runtime dependencies; prefer the standard library when sufficient.
- Do not connect to price services or execute trades. Prices are supplied as arguments, and rebalancing returns proposals only.
- Use `Decimal` for prices, quantities, values, and weights. Do not use `float` for financial calculations.
- Preserve fractional-share support and the behavior documented in `README.md`.
- Add or update tests with behavior changes. Run `make test` before finishing.
- Keep API names, code, and reviewer-facing documentation in English. These agent instructions are also in English.
- Do not add files outside the scope of this exercise.
- Do not store credentials, personal financial data, or real market quotes in the repository.

## Preferred Commands

```bash
make test
make format-check
make lint
```

See `.agents/custom_agents/backend_engineer.yaml` for the Backend Engineer role scope.
