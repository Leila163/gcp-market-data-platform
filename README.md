# MarketPulse

[![CI](https://github.com/Leila163/gcp-market-data-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/Leila163/gcp-market-data-platform/actions/workflows/ci.yml)

MarketPulse is an educational cloud data engineering project for collecting,
validating, transforming, and analyzing US equity market data.

The project uses Lam Research Corporation (`LRCX`) as an anchor for exploring
portfolio concentration, risk, and diversification scenarios. It is designed as a learning project.

## Project goals

- Ingest daily stock-market data from an external API.
- Preserve immutable raw API responses.
- Validate schemas, freshness, and corporate actions.
- Build tested analytical models for returns, volatility, and drawdown.
- Compare hypothetical portfolio allocations without exposing private holdings.
- Deploy a scheduled pipeline on Google Cloud.
- Provision cloud infrastructure reproducibly with Terraform.
- Validate code and infrastructure through GitHub Actions.

## Current status

Sprint 1 complete: tested Alpha Vantage extraction, secure configuration,
typed OHLCV transformation, and automated CI.

## Privacy

Actual holdings, API keys, downloaded data, and private configuration files are
excluded from version control. Public examples will use synthetic portfolio data.

## Disclaimer

This project is for education and analytical experimentation. It does not
provide investment advice or recommendations to buy or sell securities.
