# POE2 Market Intelligence Tool - API Research

## Executive Summary

Building a market intelligence tool for Path of Exile 2 involves leveraging several data sources. The ecosystem consists of:
1. **Official GGG APIs** - The authoritative source, but with limited POE2 support currently
2. **Third-party aggregators** - poe.ninja, poe2scout that process and expose data
3. **Community wrappers** - TypeScript/Python libraries that simplify API access

---

## 1. Official GGG APIs

### 1.1 Developer API (OAuth-based)
**Base URL:** `https://api.pathofexile.com`  
**Documentation:** https://www.pathofexile.com/developer/docs

#### POE2-Supported Endpoints

| Endpoint | Scope Required | POE2 Support |
|----------|---------------|--------------|
| `GET /character/poe2` | `account:characters` | ✅ Yes |
| `GET /character/poe2/<name>` | `account:characters` | ✅ Yes |
| `GET /league?realm=poe2` | `service:leagues` | ✅ Yes |
| `GET /currency-exchange/poe2` | `service:cxapi` | ✅ Yes |
| `GET /item-filter` | `account:item_filter` | ✅ Yes (realm=poe2) |

#### Currency Exchange API (Key for Market Data)
```
GET /currency-exchange[/poe2][/<timestamp>]
```
Returns hourly aggregate trade history:
```json
{
  "next_change_id": 1703030400,
  "markets": [{
    "league": "Dawn of the Hunt",
    "market_id": "chaos|divine",
    "volume_traded": {"chaos": 15000, "divine": 150},
    "lowest_stock": {"chaos": 100, "divine": 1},
    "highest_stock": {"chaos": 50000, "divine": 500},
    "lowest_ratio": {"chaos": 95, "divine": 1},
    "highest_ratio": {"chaos": 110, "divine": 1}
  }]
}
```

#### Limitations for POE2
- ❌ **No Public Stash API** for POE2 (PoE1 only)
- ❌ **No direct trade search API** documented (website API exists but undocumented)
- ⚠️ Currency Exchange only provides hourly historical data, not real-time

### 1.2 Undocumented Trade Site API
**Base URL:** `https://www.pathofexile.com/api/trade`

Used by the official trade site and tools like poe2scout. **Not officially documented** but widely reverse-engineered.

#### Search Endpoint
```
POST /api/trade/search/poe2/<league>
Content-Type: application/json

{
  "query": {
    "status": {"option": "online"},
    "name": "Headhunter",
    "type": "Leather Belt",
    "filters": {
      "trade_filters": {
        "filters": {
          "price": {"min": 1, "max": 100}
        }
      }
    }
  },
  "sort": {"price": "asc"}
}
```

Response returns item hashes:
```json
{
  "id": "queryId123",
  "result": ["hash1", "hash2", "hash3", ...],
  "total": 150
}
```

#### Fetch Endpoint
```
GET /api/trade/fetch/<hash1,hash2,hash3>?query=<queryId>
```

Returns full item listings with prices.

#### Exchange Endpoint (Bulk/Currency)
```
POST /api/trade/exchange/poe2/<league>
```

#### Static Data
```
GET /api/trade/data/items       # Item types
GET /api/trade/data/stats       # Stat filters  
GET /api/trade/data/static      # Currency types
GET /api/trade/data/leagues     # Active leagues
```

---

## 2. Third-Party APIs

### 2.1 POE2Scout API
**Base URL:** `https://poe2scout.com/api`  
**Documentation:** https://poe2scout.com/api/swagger  
**License:** Open API, free to use  

POE2Scout aggregates data from the official trade API and provides processed price data.

#### Key Features
- Real-time item price tracking
- Historical price data
- Currency exchange rates
- Completely open API

#### Usage Requirements
- Include `User-Agent` header with contact email
- High-volume users should contact maintainer for optimized endpoints

#### Example Endpoints (from their Swagger docs)
```
GET /api/items                    # List all tracked items
GET /api/items/{id}/prices        # Price history for item
GET /api/currencies               # Currency values
GET /api/leagues                  # Active leagues
```

### 2.2 poe.ninja API
**Base URL:** `https://poe.ninja/api/data`  
**POE2 Support:** Limited (economy section launched recently)

#### POE1 Endpoints (reference for future POE2 support)

**Currency Overview:**
```
GET /currencyoverview?league=<league>&type=Currency
GET /currencyoverview?league=<league>&type=Fragment
```

**Item Overview:**
```
GET /itemoverview?league=<league>&type=<type>
```

Types: `Oil`, `Incubator`, `Scarab`, `Fossil`, `Resonator`, `Essence`, `DivinationCard`, `SkillGem`, `BaseType`, `UniqueMap`, `Map`, `UniqueJewel`, `UniqueFlask`, `UniqueWeapon`, `UniqueArmour`, `UniqueAccessory`, `Beast`, etc.

#### Response Structure
```json
{
  "lines": [{
    "id": 636,
    "name": "House of Mirrors",
    "chaosValue": 18567,
    "exaltedValue": 822.64,
    "divineValue": 75,
    "sparkline": {"data": [...], "totalChange": -7.62},
    "listingCount": 119,
    "detailsId": "house-of-mirrors"
  }],
  "currencyDetails": [...]
}
```

#### POE2 Notes
poe.ninja recently launched POE2 economy tracking using Currency Exchange data. Their POE2 API structure may differ from POE1.

---

## 3. Existing Libraries & Wrappers

### 3.1 TypeScript/JavaScript

#### @klayver/poe-api-wrappers
```bash
npm install @klayver/poe-api-wrappers
```

```typescript
import { PathOfExile, Ninja } from "@klayver/poe-api-wrappers";

// Set user agent (required by GGG)
PathOfExile.Settings.userAgent = "my-tool/1.0 (contact@email.com)";

// Trade search
const query = {
  query: {
    status: { option: "online" },
    name: "Headhunter"
  },
  sort: { price: "asc" }
};
const search = await PathOfExile.Trade.search("Standard", query);
const results = await search.getNextItems();

// poe.ninja
const currencies = await Ninja.Currency.get("Standard", "Currency");
```

#### poe-api-ts
```bash
npm install poe-api-ts
```

Similar functionality with typed responses and class-based objects.

### 3.2 Python

#### poe_ninja_client
```bash
pip install poe-ninja-client
```

```python
from poe_ninja_client import PoENinja, CurrencyType, ItemType

with PoENinja(league="Settlers") as client:
    currency_data = client.get_currency_overview(CurrencyType.CURRENCY)
    unique_armours = client.get_item_overview(ItemType.UNIQUE_ARMOUR)
    
    # Find specific currency
    divine = client.find_currency_line("Divine Orb", CurrencyType.CURRENCY)
    print(f"Divine Orb: {divine.chaosEquivalent} chaos")
```

### 3.3 Rust

#### poe_ninja crate
```toml
[dependencies]
poe_ninja = "0.1"
```

```rust
use poe_ninja::*;

#[tokio::main]
async fn main() {
    let client = Client::new("Settlers").unwrap();
    let currencies = client.get_currencies().await.unwrap();
}
```

---

## 4. Rate Limiting

### Official API Rate Limits
GGG uses dynamic rate limits communicated via response headers:

```
X-Rate-Limit-Policy: trade-search
X-Rate-Limit-Rules: ip,account
X-Rate-Limit-Ip: 12:4:60,45:12:300
X-Rate-Limit-Ip-State: 1:4:0,1:12:0
```

Format: `requests:period_seconds:timeout_seconds`

**Best practices:**
- Parse `X-Rate-Limit-*-State` headers
- Implement exponential backoff on 429 responses
- Respect `Retry-After` header

### Third-Party Limits
- **poe2scout**: Contact maintainer for high-volume usage
- **poe.ninja**: Be respectful, cache responses

---

## 5. Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Market Tool                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Cache     │  │  Rate       │  │  Data Aggregation   │ │
│  │   Layer     │  │  Limiter    │  │  & Normalization    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Data Sources                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Official    │  │ poe2scout   │  │  poe.ninja          │ │
│  │ Trade API   │  │ API         │  │  (when POE2 ready)  │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Suggested Data Source Strategy

| Data Type | Primary Source | Fallback |
|-----------|---------------|----------|
| Real-time prices | Official Trade API | poe2scout |
| Historical prices | poe2scout | Currency Exchange API |
| Currency values | Currency Exchange API | poe2scout |
| Item metadata | Official Trade Static | poe2scout |
| Build data | Official Ladder API | - |

---

## 6. Key Implementation Notes

### Authentication
1. Register OAuth app at https://www.pathofexile.com/developer/apps
2. For public APIs (trade search), only User-Agent required
3. For private APIs, implement OAuth 2.1 flow

### User-Agent Format
```
User-Agent: OAuth <clientId>/<version> (contact: <email>)
```

### POE2 League Names
Current POE2 leagues (check dynamically):
- `Dawn of the Hunt` (current challenge league)
- `Standard` (POE2 permanent)
- `Hardcore` (POE2 permanent HC)

### Disclaimer Requirement
All public tools must display:
> "This product isn't affiliated with or endorsed by Grinding Gear Games in any way."

---

## 7. Quick Start Code Examples

### Fetch POE2 Currency Exchange Data (Official API)
```python
import requests

url = "https://api.pathofexile.com/currency-exchange/poe2"
headers = {
    "User-Agent": "MyTool/1.0 (contact@email.com)"
}

response = requests.get(url, headers=headers)
data = response.json()

for market in data.get("markets", []):
    print(f"{market['market_id']}: Volume {market['volume_traded']}")
```

### Search Trade API (Undocumented)
```python
import requests

def search_trade(league: str, item_name: str):
    search_url = f"https://www.pathofexile.com/api/trade/search/poe2/{league}"
    headers = {"User-Agent": "MyTool/1.0 (contact@email.com)"}
    
    query = {
        "query": {
            "status": {"option": "online"},
            "name": item_name
        },
        "sort": {"price": "asc"}
    }
    
    resp = requests.post(search_url, json=query, headers=headers)
    result = resp.json()
    
    # Fetch first 10 results
    hashes = result["result"][:10]
    fetch_url = f"https://www.pathofexile.com/api/trade/fetch/{','.join(hashes)}"
    items = requests.get(fetch_url, headers=headers, params={"query": result["id"]})
    
    return items.json()
```

### Use poe2scout API
```python
import requests

def get_item_prices(item_id: str):
    url = f"https://poe2scout.com/api/items/{item_id}/prices"
    headers = {"User-Agent": "MyTool/1.0 (contact@email.com)"}
    
    return requests.get(url, headers=headers).json()
```

---

## 8. Resources

| Resource | URL |
|----------|-----|
| Official Developer Docs | https://www.pathofexile.com/developer/docs |
| OAuth App Registration | https://www.pathofexile.com/developer/apps |
| POE2Scout GitHub | https://github.com/poe2scout/poe2scout |
| POE2Scout API Docs | https://poe2scout.com/api/swagger |
| poe.ninja POE2 Economy | https://poe.ninja/poe2/economy |
| poe.ninja API (unofficial) | https://github.com/ayberkgezer/poe.ninja-API-Document |
| @klayver/poe-api-wrappers | https://klayver.github.io/poe-api-wrappers |
| Awesome POE2 List | https://github.com/5k-mirrors/awesome-poe-2 |

---

## 9. Considerations

1. **API Stability**: The undocumented trade API could change without notice
2. **Rate Limits**: Plan for aggressive rate limiting during peak times
3. **Data Freshness**: Currency Exchange API has hourly delay; poe2scout may have real-time data
4. **Legal**: Follow GGG's third-party policy strictly to avoid access revocation
5. **POE2 Evolution**: APIs are still maturing for POE2; expect changes during Early Access