# Server Side

This handles code for tracking real time market prices from polymarket, kalshi, and other markets and 
converting them to a consistant representation.

## Overview:

### Server State

The core API is housed in [server_state.py](./server_state.py).
This is how we represent the data that comes in from the various markets.

### Websocket Handlers

Between the web sockets that connect directly to external API's and the server state is the [websocket_handlers](./websocket_handlers.py).
These account for each type of message that can come from the websocket clients, and convert the messages
into updated to the server state.

### Client

[kalshi_client.py](./kalshi_client.py): websocket client class for Kalshi websocket API (https://trading-api.readme.io/reference/ws).
Requires auth.

[polymarket_client.py](./polymarket_client.py): websocket client class for polymarket websocket API (https://docs.polymarket.com/developers/CLOB/websocket/wss-overview).
No auth requried.

### Misc dtypes:

Strictly typed datatypes for the internal server state, polymarket api, kalshi api, etc.

## Example:

To run the demo, pass a polymarket `token_id` and/or kalshi `ticker` as command line arguments to [main](./main.py) like so:

```
uv run main.py poly 33064224357523449786613480102704635026181428303479305990935387590344871823925 kalshi KXMAYORNYCNOMD-25-AC
```

### Polymarket _token_id_ from URL

To get token_id from polymarket, you can use the `slug` from the url. 

For example, [https://polymarket.com/event/***nyc-mayor-dem-primary-1st-round-winner***](https://polymarket.com/event/nyc-mayor-dem-primary-1st-round-winner)

Then query [https://gamma-api.polymarket.com/events?***slug=nyc-mayor-dem-primary-1st-round-winner***](https://gamma-api.polymarket.com/events?slug=nyc-mayor-dem-primary-1st-round-winner)

### Kalshi _ticker_ from URL

Similarly use the `series_ticker` from Kalshi urls to get the market `ticker`

[https://kalshi.com/markets/***kxmayornycnomd***/new-york-city-mayoral-nominations](https://kalshi.com/markets/kxmayornycnomd/new-york-city-mayoral-nominations)

Then query [https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=***KXMAYORNYCNOMD***](https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXMAYORNYCNOMD) _(MUST BE UPPER CASE)_