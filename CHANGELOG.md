# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.0] - 2025-01-06

### Initial Release 🎉

#### Features
- **Crafting Simulator**
  - Visual drag-and-drop interface for crafting
  - Support for all basic currencies (Transmutation, Augmentation, Alteration, Regal, Exalted, Chaos, Annulment, Divine, Vaal)
  - Complete essence system (12 types × 5 tiers = 60 essences)
  - Full desecration/bone system (14 bone types with tiered mods)
  - Omen system (40+ omens with complex interactions)
  - Real-time crafting simulation with retry functionality

- **Item Parser**
  - Import items from PoE2 clipboard (Ctrl+C or Ctrl+Alt+C)
  - Automatic mod detection and tier matching
  - Support for both simple and detailed formats
  - Warning system for unrecognized modifiers
  - Export items back to clipboard

- **Smart Filtering**
  - Shows only applicable currencies for current item
  - Filters omens by currency compatibility
  - Mod pool preview shows all possible mods
  - Desecration filtering by boss type

- **Crafting Mechanics**
  - Exclusion groups (mutually exclusive mods)
  - Mod group conflict detection
  - Essence-only modifiers
  - Desecrated-only modifiers
  - Tag-based filtering
  - Item level requirements
  - Boss-specific desecration (Ulaman, Kurgal, Amanamu)

#### Technical
- FastAPI backend with Pydantic validation
- React + TypeScript frontend with Vite
- JSON-based modifier database
- Comprehensive test suite (100+ tests)
- Full type safety throughout

#### Known Issues
- Some obscure modifiers may not be in the database
- Crafting history limited to current session (no persistence)
- No probability calculations yet

---

## Future Releases

See [docs/ENHANCEMENT_ROADMAP.md](docs/ENHANCEMENT_ROADMAP.md) for planned features.
