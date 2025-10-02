"""Test script to verify essence restrictions after backend restart"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1/crafting"

# Test 1: Normal item
normal_item = {
    "base_name": "Vile Robe",
    "base_category": "int_armour",
    "rarity": "Normal",
    "item_level": 82,
    "quality": 20,
    "prefix_mods": [],
    "suffix_mods": [],
    "corrupted": False
}

print("=" * 60)
print("TEST 1: Essences available for NORMAL item")
print("=" * 60)
response = requests.post(f"{BASE_URL}/currencies/available-for-item", json=normal_item)
essences = [c for c in response.json() if 'Essence' in c and 'Perfect' not in c and 'Corrupted' not in c]
print(f"Available essences (Lesser/Normal/Greater): {len(essences)}")
if essences:
    print(f"FAIL: Should be 0, but found: {essences[:5]}")
else:
    print("PASS: No Lesser/Normal/Greater essences available for Normal items")

# Test 2: Magic item
magic_item = normal_item.copy()
magic_item["rarity"] = "Magic"

print("\n" + "=" * 60)
print("TEST 2: Essences available for MAGIC item")
print("=" * 60)
response = requests.post(f"{BASE_URL}/currencies/available-for-item", json=magic_item)
essences = [c for c in response.json() if 'Essence' in c and 'Perfect' not in c and 'Corrupted' not in c]
print(f"Available essences (Lesser/Normal/Greater): {len(essences)}")
if essences:
    print(f"PASS: Found {len(essences)} essences including: {essences[:3]}")
else:
    print("FAIL: Should have essences available for Magic items")

# Test 3: Try to apply essence to Normal item
print("\n" + "=" * 60)
print("TEST 3: Apply Lesser Essence to NORMAL item (should fail)")
print("=" * 60)
response = requests.post(f"{BASE_URL}/simulate", json={
    "item": normal_item,
    "currency_name": "Lesser Essence of Enhancement"
})
result = response.json()
print(f"Success: {result['success']}")
print(f"Message: {result['message']}")
if not result['success'] and "Magic" in result['message']:
    print("PASS: Correctly rejected Normal item")
else:
    print("FAIL: Should reject Normal items with message about Magic items")

# Test 4: Apply essence to Magic item
print("\n" + "=" * 60)
print("TEST 4: Apply Lesser Essence to MAGIC item (should work)")
print("=" * 60)
response = requests.post(f"{BASE_URL}/simulate", json={
    "item": magic_item,
    "currency_name": "Lesser Essence of Enhancement"
})
result = response.json()
print(f"Success: {result['success']}")
print(f"Message: {result['message']}")
if result['success']:
    new_rarity = result.get('item', {}).get('rarity')
    print(f"New rarity: {new_rarity}")
    print("PASS: Successfully applied essence to Magic item" if new_rarity == "Rare" else "PARTIAL: Applied but rarity unexpected")
else:
    print(f"FAIL: Should work on Magic items")
