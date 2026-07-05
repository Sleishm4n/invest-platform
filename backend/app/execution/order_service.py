"""
Order placement service — the ONLY entry point for turning a model
recommendation into a real (or simulated) trade.

NOT YET IMPLEMENTED — placeholder marking where M9 work lands.

Planned flow for place_order(strategy_run_id, ticker, amount_gbp):
  1. Look up `strategy_run_id` in the executed_orders table.
     If found -> log a warning, return the existing record, do NOT call the API.
  2. If settings.dry_run is True -> build the request payload, log it,
     write an executed_orders row with simulated=True, return without
     touching the network.
  3. Otherwise -> call T212Client.place_market_order(...), then immediately
     persist the response (order id, timestamp, payload) to executed_orders
     linked to the prediction_id that triggered it.
"""

# TODO(M9): implement OrderService.place_order() per the flow above
