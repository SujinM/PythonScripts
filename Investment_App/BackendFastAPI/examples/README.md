# Examples

Standalone scripts for exploring and testing eToro API endpoints directly.

Available examples:
- `etoro_instrument_types.py` — list all instrument types exposed by the eToro Public API.
- `etoro_portfolio.py` — inspect open positions with optional metadata and live rates.
- `etoro_candles.py` — fetch OHLC candle data for a single instrument ID.
- `etoro_rates.py` — fetch live bid/ask quote data for one or more instrument IDs.
- `etoro_watchlists.py` — fetch watchlists for the authenticated eToro user.

---

## etoro_instrument_types.py

Fetch all available instrument types and their IDs from the eToro Public API.

**Endpoint:**
```
GET https://public-api.etoro.com/api/v1/market-data/instrument-types
```

**Required headers:**

| Header | Description |
|---|---|
| `x-request-id` | Any unique string — UUID is auto-generated per run |
| `x-api-key` | Your eToro Public API key |
| `x-user-key` | Your eToro user key |

**Setup:**

Set your credentials in `BackendFastAPI/.env`:
```ini
ETORO_API_KEY=your_api_key
ETORO_USER_KEY=your_user_key
```

Or export them as environment variables before running.

**Usage:**
```bash
cd Investment_App/BackendFastAPI

# Formatted table output
python examples/etoro_instrument_types.py

# Raw JSON response
python examples/etoro_instrument_types.py --raw
```

**Example output:**
```
Fetching instrument types from:
  https://public-api.etoro.com/api/v1/market-data/instrument-types

Status: 200
ID  Name         Local Mapping
-----------------------------
1   Forex        Forex
2   Commodities  Commodities
4   Indices      Indices
5   Stocks       Stocks
6   ETFs         ETFs
10  Crypto       Crypto

Total instrument types: 6
Local map is in sync with the API.
```

The script also compares the API response against the local `ETORO_INSTRUMENT_TYPES` map defined in `TradeView/src/types/etoroInstrument.ts` and reports any differences.

---

## etoro_candles.py

Fetch candle data for a single eToro instrument and print either the raw JSON response or a compact OHLC table.

**Endpoint used:**
```
GET https://public-api.etoro.com/api/v1/market-data/instruments/candles
```

**Required headers:**

| Header | Description |
|---|---|
| `x-request-id` | Any unique string — UUID is auto-generated per run |
| `x-api-key` | Your eToro Public API key |
| `x-user-key` | Your eToro user key |

**Usage:**
```bash
cd Investment_App/BackendFastAPI

# One month of candles for a single instrument
python examples/etoro_candles.py --instrument-id 1001

# One year of candles
python examples/etoro_candles.py --instrument-id 1001 --period OneYear

# Show more rows in the table output
python examples/etoro_candles.py --instrument-id 1001 --limit 20

# Print the raw JSON response
python examples/etoro_candles.py --instrument-id 1001 --raw
```

**Example output:**
```
Fetching candles from:
  https://public-api.etoro.com/api/v1/market-data/instruments/candles
Instrument ID: 1001
Period: OneMonth

Time          Open      High       Low     Close    Volume
----------------------------------------------------------
1717027200  176.1200  177.8400  175.5400  177.1200  1254389
1717113600  177.1800  178.3000  176.4200  177.9500  1049281
1717200000  178.0400  179.2100  177.8800  178.6700   982114

Displayed 3 of 30 candles.
```

If the response shape differs for a specific instrument or period, rerun with `--raw` to inspect the exact payload.

---

## etoro_rates.py

Fetch live quote data for one or more eToro instrument IDs and print either the raw JSON response or a compact rates table.

**Endpoint used:**
```
GET https://public-api.etoro.com/api/v1/market-data/instruments/rates
```

**Required headers:**

| Header | Description |
|---|---|
| `x-request-id` | Any unique string — UUID is auto-generated per run |
| `x-api-key` | Your eToro Public API key |
| `x-user-key` | Your eToro user key |

**Usage:**
```bash
cd Investment_App/BackendFastAPI

# One instrument
python examples/etoro_rates.py --instrument-ids 1001

# Multiple instruments in one request
python examples/etoro_rates.py --instrument-ids 1001,9425,100001

# Print the raw JSON response
python examples/etoro_rates.py --instrument-ids 1001,9425 --raw
```

**Example output:**
```
Fetching live rates from:
  https://public-api.etoro.com/api/v1/market-data/instruments/rates
Instrument IDs: 1001,9425,100001

Instrument      Bid        Ask       Last     Change  %Change   Volume
---------------------------------------------------------------------
1001         177.1200   177.1800   177.1200    1.2400    0.70  1254389
9425       68450.2500 68480.7500 68462.5000  825.5000    1.22   284112
100001         1.0834     1.0835     1.0834    0.0021    0.19  9876543

Rates returned: 3
```

This is the simplest way to inspect the raw fields the eToro rates endpoint returns before wiring them into backend or frontend quote models.

---

## etoro_watchlists.py

Fetch watchlists for the authenticated eToro user and print either the raw JSON response or a compact summary table.

**Endpoint used:**
```
GET https://public-api.etoro.com/api/v1/watchlists
```

**Required headers:**

| Header | Description |
|---|---|
| `x-request-id` | Any unique string — UUID is auto-generated per run |
| `x-api-key` | Your eToro Public API key |
| `x-user-key` | Your eToro user key |

**Usage:**
```bash
cd Investment_App/BackendFastAPI

# Default watchlists request
python examples/etoro_watchlists.py

# Increase per-watchlist item limit and include related assets
python examples/etoro_watchlists.py --items-per-page 200 --add-related-assets

# Exclude built-in watchlists
python examples/etoro_watchlists.py --no-ensure-builtin

# Print the raw JSON response
python examples/etoro_watchlists.py --raw
```

**Example output:**
```
Fetching watchlists from:
  https://public-api.etoro.com/api/v1/watchlists
itemsPerPageForSingle: 100
ensureBuiltinWatchlists: true
addRelatedAssets: false

Watchlist ID   Name           Type     Items  Default  Related
--------------------------------------------------------------
wl_12345       Favorites      Static      12     True        0
wl_67890       Tech Stocks    Static       8    False        0
wl_24680       Crypto         Static      15    False        0

Watchlists returned: 3
Meta: page=1, itemsPerPage=100, maxItemsInWatchlist=1000, maxWatchlists=10
```

This is useful for inspecting the raw watchlist payload before wiring watchlists into backend or frontend account views.

---

## etoro_portfolio.py

Fetch all currently invested instruments (stocks, ETFs, crypto, forex, etc.) from your eToro account and display them as a formatted table with P&L data.

**Endpoints used:**

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/trading/info/real/pnl` | Open positions + unrealised P&L |
| `GET /api/v1/market-data/instruments` | Instrument display name + type |
| `GET /api/v1/market-data/instruments/rates` | Live bid prices |

**Usage:**
```bash
cd Investment_App/BackendFastAPI

# All open positions (all types)
python examples/etoro_portfolio.py

# Filter by instrument type
python examples/etoro_portfolio.py --type Stocks
python examples/etoro_portfolio.py --type ETF
python examples/etoro_portfolio.py --type Crypto
python examples/etoro_portfolio.py --type Forex
python examples/etoro_portfolio.py --type Commodity

# Raw JSON from the P&L endpoint
python examples/etoro_portfolio.py --raw

# Skip metadata/rates enrichment (faster, less info)
python examples/etoro_portfolio.py --no-enrich
```

**Example output:**
```
Fetching open positions from:
  https://public-api.etoro.com/api/v1/trading/info/real/pnl

Open positions found: 12
Fetching metadata for 12 instruments...
Fetching live rates...

Instrument         Type    Dir        Invested   Open Rate     Current     Net P&L
----------------------------------------------------------------------------------
Apple Inc.         Stocks  BUY          500.00    172.3000    185.4200      +65.23
iShares S&P 500    ETF     BUY          300.00    450.1200    467.8800      +11.80
Bitcoin            Crypto  BUY          200.00  42000.0000  45200.0000     +15.24
----------------------------------------------------------------------------------
TOTAL                                  1000.00                              +92.27

Positions shown: 3

--- By Instrument Type ---
  Crypto         1 positions  invested:     200.00  P&L:     +15.24
  ETF            1 positions  invested:     300.00  P&L:     +11.80
  Stocks         1 positions  invested:     500.00  P&L:     +65.23
```
