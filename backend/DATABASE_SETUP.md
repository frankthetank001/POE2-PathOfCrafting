# Database Setup and Data Loading Guide

This document explains how to rebuild the PoE2 TradeCraft database from scratch and load all crafting data.

## Quick Start (Rebuild Everything)

To completely rebuild the database with all data:

```bash
cd backend
python scripts/create_tables.py
python scripts/populate_complete_crafting_data.py
```

## Database Architecture

The system uses SQLite with SQLAlchemy ORM. All crafting data is stored in `backend/poe2tradecraft.db`.

### Tables Structure

1. **base_items** - All item bases (body armour, weapons, etc.)
2. **modifiers** - All modifiers including regular, essence-only, and desecrated
3. **essences** - All essence types and tiers
4. **essence_item_effects** - Item-specific essence effects
5. **omens** - All omen types
6. **omen_rules** - Omen-specific rules and effects
7. **desecration_bones** - All desecration bone types
8. **modifier_pools** - Modifier pool definitions
9. **pool_modifiers** - Modifier-to-pool associations
10. **currency_configs** - All currency configurations
11. **crafting_projects** - Saved crafting projects

## Data Sources

All data is loaded from JSON files in `backend/source_data/`:

- `item_bases.json` - 434 unique base items
- `modifiers.json` - 1,119 base modifiers
- `desecrated_modifiers.json` - 19 desecrated-only modifiers
- `currency_configs.json` - 115 currency configurations
- `essences.json` - 81 essences
- `essence_item_effects.json` - 229 item-specific essence effects
- `omens.json` - 44 omens
- `desecration_bones.json` - 11 desecration bones

## Step-by-Step Rebuild Process

### 1. Create Database Tables

```bash
python backend/scripts/create_tables.py
```

This will:
- Drop all existing tables if they exist
- Create fresh tables with proper schema
- Set up indexes for performance

Expected output:
```
Creating database tables...
Dropping existing tables...
Creating fresh tables...
Successfully created all database tables!

Created tables:
  - base_items
  - modifiers
  - essences
  - essence_item_effects
  - omens
  - omen_rules
  - desecration_bones
  - modifier_pools
  - pool_modifiers
  - currency_configs
  - crafting_projects
```

### 2. Populate All Data

```bash
python backend/scripts/populate_complete_crafting_data.py
```

This will load all data from the JSON files in `backend/source_data/`.

Expected output:
```
Starting COMPLETE crafting data population from JSON files...
Loading all data from backend/source_data/
Clearing existing crafting data...
Cleared existing data
Loading 439 base items...
Loaded 434 unique base items (from 439 entries)
Loading 1891 base modifiers...
Loaded 1119 unique base modifiers (from 1891 entries)
Loading 19 desecrated modifiers...
Loaded 19 desecrated modifiers
Desecrated modifiers per item type:
  body_armour: 10 modifiers
  boots: 10 modifiers
  charm: 15 modifiers
Loading 115 currency configurations...
Loaded 115 currency configurations
Loading 81 essences...
Loading 229 essence item effects...
Loaded 229 essence item effects
Completed loading essences and effects
Loading 44 omens...
Completed loading 44 omens
Loading 11 desecration bones...
Loaded 11 desecration bones

==================================================
COMPLETE CRAFTING DATA LOADED SUCCESSFULLY!
==================================================
Base Items: 434
Modifiers: 1138 (including desecrated)
Currency Configs: 115
Essences: 81
Omens: 44
Desecration Bones: 11
==================================================
The comprehensive PoE2 crafting system is ready!
```

## Verifying the Database

### Check Total Counts

```python
import sqlite3

conn = sqlite3.connect('backend/poe2tradecraft.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM base_items')
print(f'Base items: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(*) FROM modifiers')
print(f'Total modifiers: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(*) FROM essences')
print(f'Essences: {cursor.fetchone()[0]}')

conn.close()
```

### Check Desecrated Modifiers

Desecrated modifiers are stored in the main `modifiers` table with these identifying characteristics:
- `weight = 1`
- `tier = 1`
- `required_ilvl = 65`
- `mod_type = 'suffix'`
- `tags` contains `"desecrated_only"`

To verify via SQLAlchemy:

```python
from app.models.base import get_db
from app.models.crafting import Modifier

db = next(get_db())

desecrated = db.query(Modifier).filter(
    Modifier.weight == 1,
    Modifier.tier == 1,
    Modifier.required_ilvl == 65,
    Modifier.mod_type == 'suffix'
).count()

print(f'Desecrated modifiers: {desecrated}')  # Should be 19
```

## Adding New Data

### Adding New Desecrated Modifiers

Use the template script `backend/scripts/desecrated_mod_template.py` to add new desecrated modifiers, then regenerate the JSON:

```bash
python backend/scripts/create_desecrated_modifiers.py
```

This will update `backend/source_data/desecrated_modifiers.json`.

### Updating Other Data

1. Modify the appropriate JSON file in `backend/source_data/`
2. Re-run the populate script:
   ```bash
   python backend/scripts/populate_complete_crafting_data.py
   ```

## Troubleshooting

### Issue: Duplicate Key Errors

The populate script handles duplicates by checking for existing entries before insertion. If you get duplicate errors, the database may be corrupted. Solution:

```bash
# Start fresh
python backend/scripts/create_tables.py
python backend/scripts/populate_complete_crafting_data.py
```

### Issue: Missing Desecrated Modifiers

Desecrated modifiers won't show up in direct SQLite queries on the JSON `tags` column. Use SQLAlchemy ORM or query by their unique characteristics (weight=1, tier=1, ilvl=65).

### Issue: Database Locked

If the database is locked, ensure no other processes are accessing it:
- Stop the backend server
- Close any database viewers
- Try the operation again

## Backup and Restore

### Create Backup

```bash
cp backend/poe2tradecraft.db backend/poe2tradecraft_backup.db
```

### Restore from Backup

```bash
cp backend/poe2tradecraft_backup.db backend/poe2tradecraft.db
```

### Export to JSON (Full Backup)

All data is already exported to JSON files in `backend/source_data/`. These serve as the source of truth and can be version controlled.

## Development Notes

- The database uses the Smart Hybrid Architecture: mechanics in code, content in database
- All modifiers (regular, essence-only, desecrated) are stored in the single `modifiers` table
- The `DesecrationModifier` model was removed as legacy - do not re-add it
- Frontend retrieves desecrated modifiers by filtering for the `"desecrated_only"` tag

## Related Scripts

- `backend/scripts/create_tables.py` - Creates database schema
- `backend/scripts/populate_complete_crafting_data.py` - Loads all data from JSON
- `backend/scripts/create_desecrated_modifiers.py` - Generates desecrated modifiers JSON
- `backend/scripts/desecrated_mod_template.py` - Template for adding new desecrated modifiers