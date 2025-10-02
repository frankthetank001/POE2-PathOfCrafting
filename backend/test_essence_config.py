"""Check essence config from API"""
import requests
import json

# Test getting essence info
response = requests.get("http://localhost:8000/api/v1/crafting/currencies/categorized")
data = response.json()

print("=== Checking Essence Configuration ===\n")

# Get an essence from available currencies
response2 = requests.post("http://localhost:8000/api/v1/crafting/currencies/available-for-item", json={
    "base_name": "Vile Robe",
    "base_category": "int_armour",
    "rarity": "Normal",
    "item_level": 82,
    "quality": 20,
    "prefix_mods": [],
    "suffix_mods": [],
    "corrupted": False
})

available = response2.json()
lesser_essences = [c for c in available if c.startswith("Lesser Essence")]

print(f"Available for Normal item: {len(lesser_essences)} Lesser Essences")
print(f"First 3: {lesser_essences[:3]}\n")

# Try to apply one
test_essence = "Lesser Essence of Enhancement"
print(f"=== Testing {test_essence} ===\n")

response3 = requests.post("http://localhost:8000/api/v1/crafting/simulate", json={
    "item": {
        "base_name": "Vile Robe",
        "base_category": "int_armour",
        "rarity": "Normal",
        "item_level": 82,
        "quality": 20,
        "prefix_mods": [],
        "suffix_mods": [],
        "corrupted": False
    },
    "currency_name": test_essence
})

result = response3.json()
print(f"Success: {result['success']}")
print(f"Message: {result['message']}\n")

if not result['success']:
    if "Magic" in result['message']:
        print("✓ PASS: Correctly requires Magic items")
    elif "No suitable" in result['message']:
        print("✗ FAIL: Passed rarity check but failed to find mods")
        print("  This suggests mechanic field is NULL/empty in database")
        print("\n  SOLUTION: Run the populate script:")
        print("  cd backend")
        print("  python scripts/populate_complete_crafting_data.py")
    else:
        print(f"✗ FAIL: Unexpected error")
else:
    print("✗ FAIL: Should not work on Normal items!")
