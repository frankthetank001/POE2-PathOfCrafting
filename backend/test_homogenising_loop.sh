#!/bin/bash
for i in 1 2 3 4 5; do
  echo "=== Application $i ==="
  result=$(curl -s "http://localhost:8000/api/v1/crafting/simulate-with-omens" -H "Content-Type: application/json" -d @/tmp/test_item.json)
  echo "$result" | python -c "
import sys, json
r = json.load(sys.stdin)
print(f\"Success: {r['success']}\")
print(f\"Message: {r['message']}\")
item = r.get('result_item')
if item:
    prefixes = len(item['prefix_mods'])
    suffixes = len(item['suffix_mods'])
    print(f\"State: {prefixes} prefixes, {suffixes} suffixes\")
    
    all_mods = item['prefix_mods'] + item['suffix_mods']
    existing_tags = set()
    for m in all_mods[:-1]:
        if m.get('tags'):
            existing_tags.update(m['tags'])
    
    added = all_mods[-1] if all_mods else None
    if added:
        print(f\"Added: {added['name']} ({added['mod_type']}) with tags: {added.get('tags', [])}\")
        if existing_tags:
            has_match = any(t in existing_tags for t in added.get('tags', []))
            print(f\"Matches existing tags {list(existing_tags)}: {'YES' if has_match else 'NO'}\")
"
  
  # Save state for next iteration
  echo "$result" | python -c "import sys, json; r=json.load(sys.stdin); item=r.get('result_item'); print(json.dumps({'item': item, 'currency_name': 'Perfect Exalted Orb', 'omen_names': ['Omen of Homogenising Exaltation']}))" > /tmp/test_item.json
  echo ""
done
