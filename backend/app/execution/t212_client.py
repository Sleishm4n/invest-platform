"""
Trading 212 API client.

NOT YET IMPLEMENTED — this is a placeholder marking where M9 work lands.
Design constraints agreed for this module (see docs/architecture.md):

- Single class, base URL selected via `settings.t212_base_url` (demo vs live) —
  the SAME code path is used for paper trading (M8) and real trading (M9).
- Every order-placing call must go through OrderService, never called directly,
  so the idempotency guard can't be bypassed.
- API key/secret read from settings, never hardcoded or logged.
"""

# TODO(M9): implement T212Client with get_account_summary(), get_instruments(),
# place_market_order(), get_order_history()
