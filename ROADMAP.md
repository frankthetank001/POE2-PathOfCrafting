# 🗺️ Path of Crafting - Development Roadmap

This roadmap outlines completed features and planned enhancements for POE2 - Path of Crafting.

---

## 🎯 High-Level Roadmap

### ✅ Core Features (Completed)

**Crafting System**
- Complete crafting mechanics for all currency types
- Essences (all tiers: Lesser, Normal, Greater, Perfect, Corrupted)
- Omens with complex interactions
- Desecration system (all bone types)
- Fracturing orbs
- Annulment, Exalted, Chaos, Divine, Vaal, and all basic currencies
- Support for all item types and categories

**Modifiers & Data**
- 1,100+ modifier database with proper grouping
- Modifier groups and exclusion rules
- Modifier tiers with accurate value ranges
- Weight conditions for item-specific mod pools

**User Experience**
- Item import/export (in-game parser, PoB format, trade format)
- Undo/Redo functionality (Ctrl+Z, Ctrl+R, Ctrl+Y)
- Currency expenditure tracking
- Crafting history with step-by-step review

---

### 📋 Planned Features

**Phase 1: AI Assistant (Q1 2026)**
- AI chatbot for crafting guidance
- Automated crafting execution
- Intelligent strategy recommendations

**Phase 2: Market Intelligence (Q2 2026)**
- Real-time pricing estimations
- Trade site integration
- Item value calculator

**Phase 3: Build Intelligence (Q3 2026)**
- Popular build analysis from poe.ninja
- Trending items and modifiers
- Build-specific crafting recommendations

---

## ✅ Detailed Feature List (v0.1.0-beta)

### Core Crafting Simulator
✅ **Visual Grid-Based Interface** - Intuitive crafting workspace with item display and currency stash
✅ **Real-Time Crafting Simulation** - Apply currencies and see instant results
✅ **Complete Crafting Mechanics Implementation**:
  - Basic currencies (Transmutation, Augmentation, Alchemy, Regal, Exalted, Chaos, Annulment, Divine, Fracturing)
  - All essence tiers (Lesser, Normal, Greater, Perfect, Corrupted)
  - 12 essence types with item-specific effects
  - Essence of the Abyss (Mark of the Abyssal Lord)
  - 14 desecration bone types (Ancient, Preserved, Gnawed variants)
  - 40+ omens with complex interactions
  - Fracturing mechanics
  - Corruption mechanics

### Item Management
✅ **Item Creation** - Create base items with customizable item level and quality
✅ **Item Import/Export** - Copy items from game (Ctrl+C) and parse automatically
✅ **Item Parser** - Detects mods, tiers, and values from in-game item text
✅ **Warning System** - Alerts for unrecognized modifiers

### Smart Features
✅ **Available Currency Filtering** - Only shows currencies valid for current item state
✅ **Compatible Omen Filtering** - Shows omens that work with selected currency
✅ **Mod Pool Preview** - View all available modifiers for current item
✅ **Desecration Mod Filtering** - See which bones add which desecrated mods
✅ **Crafting History** - Step-by-step tracking with retry functionality

### Advanced Mechanics
✅ **Exclusion Groups** - Mutually exclusive modifier enforcement
✅ **Mod Group Conflicts** - Prevents duplicate mod groups
✅ **Tag-Based Filtering** - Homogenising omens with tag matching
✅ **Item Level Requirements** - Enforces ilvl restrictions for mods
✅ **Weight Conditions** - Item-specific modifier weights
✅ **Essence-Only Mods** - Special mods only from essences
✅ **Desecrated-Only Mods** - Boss-specific desecration modifiers

### Data & Infrastructure
✅ **Comprehensive Modifier Database** - 1,100+ base modifiers
✅ **Complete Essence Database** - All tiers and item effects
✅ **Omen Rules Engine** - Complex omen interaction logic
✅ **Base Item Library** - All craftable item bases
✅ **Docker Deployment** - Production-ready containerization
✅ **CI/CD Pipeline** - Automated testing and deployment
✅ **RESTful API** - FastAPI backend with full documentation

---

## 🚧 In Progress

### UI/UX Improvements
📋 **Active Tab Highlighting** - Better navigation visual feedback
📋 **Currency Tooltips** - Detailed information on hover
📋 **Responsive Design** - Mobile and tablet optimization
📋 **Theme Customization** - Light/dark mode toggle

---

## 🔮 Planned Features

### Phase 1: AI Crafting Assistant (Q1 2026)
**Goal**: Intelligent crafting guidance with automated execution

📋 **AI Chatbot Interface**
  - Natural language interaction ("Help me craft a +3 spell skills amulet")
  - Context-aware suggestions based on current item
  - Step-by-step crafting guidance

📋 **Automated Crafting Execution**
  - AI can apply currencies directly to your item
  - Multi-step crafting plans with automatic execution
  - "Craft this for me" mode - set budget and target, let AI optimize

📋 **Intelligent Strategy Recommendations**
  - Probability calculations for target mods
  - Cost-benefit analysis (expected currency cost)
  - Alternative crafting paths comparison

📋 **Learning System**
  - Remembers user preferences and common crafting goals
  - Adapts suggestions based on past crafting sessions

**Tech Stack**: LLM integration (Anthropic/OpenAI), vector database for crafting knowledge

---

### Phase 2: Market Intelligence (Q2 2026)
**Goal**: Real-world pricing data for crafted items

📋 **Trade Site Integration**
  - Lookup current market prices for similar items
  - Price estimation for crafted items
  - Historical pricing trends

📋 **Item Value Calculator**
  - Estimate value based on modifier combinations
  - Compare crafting cost vs. market price
  - ROI analysis ("Is this craft profitable?")

📋 **Price Alerts**
  - Track specific item types and alert on price changes
  - Identify undervalued crafting opportunities

📋 **Bulk Currency Pricing**
  - Current exchange rates for essences, omens, bones
  - Calculate total crafting cost in Divines/Exalts

**Data Sources**: poe.trade, pathofexile.com/trade API (if available), community price aggregators

---

### Phase 3: Build Intelligence (Q3 2026)
**Goal**: Data-driven crafting suggestions from popular builds

📋 **Popular Build Indexing**
  - Scrape/aggregate builds from poe.ninja
  - Parse build data for common item configurations
  - Identify meta modifier combinations

📋 **Build-Based Recommendations**
  - "Show me popular crafts for Spark builds"
  - High-value modifier suggestions per build archetype
  - Build comparison (Sorceress vs. Warrior item priorities)

📋 **Meta Analysis Dashboard**
  - Most crafted item types by build
  - Trending modifier combinations
  - League-specific crafting meta

📋 **Smart Crafting Goals**
  - "Craft for Poison Concoction" → suggests relevant mods
  - Budget-based build recommendations
  - Tier lists for modifier importance per build type

**Data Sources**: poe.ninja builds API, community build aggregators, ladder data

---

### Phase 4: Advanced Features (2027)

#### Crafting Scenarios
📋 **Benchmark Mode** - Compare crafting outcomes across 10,000+ simulations
📋 **Cost Optimizer** - Find cheapest path to target modifiers
📋 **Mirror Service Helper** - Design and optimize mirror-tier items

#### Social Features
📋 **Crafting Guides** - Community-created crafting tutorials
📋 **Share Crafting Sessions** - Export/import crafting histories
📋 **Leaderboards** - Best crafts by category

#### Economy Tools
📋 **Profit Calculator** - Bulk crafting profitability analysis
📋 **Essence/Omen Arbitrage** - Identify mispriced currencies
📋 **League Starter Crafting** - Budget crafting guides for league start

#### Integration & Automation
📋 **PoE2 Overlay** - In-game overlay integration (if permitted)

---

## 🎯 Long-Term Vision

**Path of Crafting** aims to become the definitive crafting companion for Path of Exile 2:

1. **Accuracy**: Always match in-game mechanics 1:1
2. **Intelligence**: AI-powered guidance that understands player goals
3. **Community**: Shared knowledge base of successful crafts
4. **Value**: Help players make informed crafting decisions and avoid wasted currency

---

## 📊 Success Metrics

- **Simulation Accuracy**: 99.9%+ match with in-game results
- **User Engagement**: 10,000+ monthly active users (post-AI launch)
- **Community Growth**: 100+ community-submitted crafting guides
- **Market Integration**: 90%+ pricing accuracy vs. actual trade listings

---

## 🤝 Community Feedback

We actively collect feedback on:
- Missing mechanics or incorrect simulations
- Feature requests and priority votes
- Build-specific crafting needs
- Performance and UX improvements

**Submit feedback**: [GitHub Issues](https://github.com/yourusername/Poe2-PathOfCrafting/issues)

---

## 📅 Release Schedule

| Version | Target Date | Focus |
|---------|------------|-------|
| **v0.1.0** | Current (Oct 2025) | Core crafting mechanics (beta) |
| **v0.2.0** | Q4 2025 | UI/UX polish, mobile support |
| **v1.0.0** | Q1 2026 | AI crafting assistant launch |
| **v1.5.0** | Q2 2026 | Market intelligence integration |
| **v2.0.0** | Q3 2026 | Build intelligence system |

---

*This roadmap is subject to change based on community feedback, PoE2 development updates, and technical constraints.*

**Last Updated**: October 2025
