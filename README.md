# PoE2 TradeCraft

**A crafting simulator and theory-crafting tool for Path of Exile 2**

Plan your perfect items with accurate simulation of all crafting mechanics, essences, desecration, and omens.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![React](https://img.shields.io/badge/react-18+-blue.svg)

## ✨ Features

### 🎲 Crafting Simulator
- **Visual crafting interface** - Drag and drop currencies, essences, and bones to simulate crafting
- **Real-time feedback** - See exactly what will happen before you spend your currency
- **Accurate mechanics** - All PoE2 crafting mechanics implemented:
  - Basic currencies (Transmutation, Augmentation, Regal, Exalted, Chaos, etc.)
  - All essence tiers (Lesser, Normal, Greater, Perfect, Corrupted)
  - Desecration system (14 bone types with level/ilvl restrictions)
  - Omen system (40+ omens with complex interactions)
  - Exclusion groups and mod conflicts

### 📋 Item Import/Export
- **Copy from game** - Paste items directly from PoE2 (Ctrl+C or Ctrl+Alt+C)
- **Automatic parsing** - Detects mods, tiers, and values
- **Warning system** - Alerts you if modifiers aren't recognized
- **Export back** - Copy finished items to share or compare

### 🎯 Smart Filtering
- **Available currencies** - Only shows currencies that work on your current item
- **Compatible omens** - Filters omens by currency type
- **Mod pool preview** - See all possible mods you can roll
- **Desecration filtering** - Shows which bones add which desecrated mods

### 📊 Crafting History
- **Step-by-step tracking** - Review every crafting action
- **Retry system** - Go back and try different outcomes
- **Compare results** - Test different crafting paths

## 🚀 Quick Start

### Prerequisites

**Option 1: Docker (Recommended)**
- Docker Desktop (includes Docker and Docker Compose)

**Option 2: Manual Installation**
- Python 3.11 or higher
- Node.js 18 or higher

### Installation

#### 🐳 Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Poe2-AI-TradeCraft.git
   cd Poe2-AI-TradeCraft
   ```

2. **Start the application**
   ```bash
   # Development mode with hot reload
   docker-compose up

   # Or run in background
   docker-compose up -d
   ```

   - Backend will run at `http://localhost:8000`
   - Frontend will run at `http://localhost:5173`

3. **Open your browser**

   Navigate to `http://localhost:5173` and start crafting!

4. **Stop the application**
   ```bash
   docker-compose down
   ```

#### 🔧 Manual Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Poe2-AI-TradeCraft.git
   cd Poe2-AI-TradeCraft
   ```

2. **Start the backend**
   ```bash
   cd backend
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Mac/Linux
   source venv/bin/activate

   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

   Backend will run at `http://localhost:8000`

3. **Start the frontend** (in a new terminal)
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

   Frontend will run at `http://localhost:5173`

4. **Open your browser**

   Navigate to `http://localhost:5173` and start crafting!

#### 🚀 Production Deployment

For production deployment with optimizations:

```bash
# Build and run production images
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop production deployment
docker-compose -f docker-compose.prod.yml down
```

Production frontend will run on port `80`, backend on port `8000`.

## 📖 Usage

### Creating an Item
1. Click "Create New Item"
2. Choose your base item (e.g., "Gold Amulet")
3. Set item level and quality

### Importing an Item
1. Copy an item from PoE2 (Ctrl+C in-game)
2. Click "Import from Clipboard"
3. Review the parsed mods and import

### Crafting
1. Your item is displayed in the center
2. Currency stash on the right shows available currencies/essences/bones
3. Click a currency to apply it
4. See the result instantly
5. Use "Retry" to try again with different RNG

### Using Omens
1. Click on a currency in the stash
2. Available omens appear below
3. Select omens to modify the crafting behavior
4. Apply the currency + omens together

## 🎮 Supported Mechanics

### Currencies
- ✅ Orb of Transmutation
- ✅ Orb of Augmentation
- ✅ Orb of Alteration
- ✅ Regal Orb
- ✅ Exalted Orb
- ✅ Chaos Orb
- ✅ Orb of Annulment
- ✅ Divine Orb
- ✅ Vaal Orb
- ✅ And more...

### Essences
- ✅ All 12 essence types (Insulation, Body, Flames, etc.)
- ✅ All 5 tiers (Lesser, Normal, Greater, Perfect, Corrupted)
- ✅ Item-specific effects
- ✅ Essence of the Abyss (Mark of the Abyssal Lord)

### Desecration (Bones)
- ✅ All 14 bone types (Jawbone, Rib, Skull, etc.)
- ✅ Tiered desecrated mods (Ancient, Preserved, Gnawed)
- ✅ Boss-specific mods (Ulaman, Kurgal, Amanamu)
- ✅ Level and item level restrictions

### Omens
- ✅ Homogenising omens (tag-based mod selection)
- ✅ Crystallisation omens (prefix/suffix targeting)
- ✅ Amplifying omens (boss-specific desecration)
- ✅ Abyssal Echoes (desecration reroll)
- ✅ Omen stacking and interactions

### Special Mechanics
- ✅ Exclusion groups (mutually exclusive mods)
- ✅ Mod group conflicts
- ✅ Essence-only mods
- ✅ Desecrated-only mods
- ✅ Tag-based filtering
- ✅ Item level requirements

## 🛠️ Development

### Running Tests
```bash
cd backend
pytest
```

### Tech Stack
- **Backend**: Python, FastAPI, Pydantic
- **Frontend**: React, TypeScript, Vite
- **Data**: JSON-based modifier database

### Project Structure
```
Poe2-AI-TradeCraft/
├── backend/              # Python FastAPI server
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── services/    # Crafting mechanics
│   │   └── source_data/ # Modifiers, essences, omens
│   └── tests/           # Test suite
├── frontend/            # React application
│   └── src/
│       ├── pages/       # Main simulator UI
│       └── services/    # API client
└── docs/                # Technical documentation
```

## 📚 Documentation

- [Crafting System Design](docs/CRAFTING_SYSTEM_DESIGN.md)
- [Exclusion Groups](docs/EXCLUSION_IMPLEMENTATION.md)
- [Enhancement Roadmap](docs/ENHANCEMENT_ROADMAP.md)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This is a fan-made tool and is not affiliated with or endorsed by Grinding Gear Games.
Path of Exile 2 is a trademark of Grinding Gear Games.

## 🙏 Acknowledgments

- Grinding Gear Games for Path of Exile 2
- poe2db.tw for item and modifier data
- The PoE community for feedback and testing

---

**Note**: PoE2 is in Early Access. Crafting mechanics may change. This tool is updated regularly to match the latest game version.
