#!/bin/bash

echo "Testing bone icon URLs..."
echo ""

urls=(
  "Ancient_Collarbone:https://www.poe2wiki.net/images/2/29/Ancient_Collarbone_inventory_icon.png"
  "Ancient_Jawbone:https://www.poe2wiki.net/images/7/79/Ancient_Jawbone_inventory_icon.png"
  "Ancient_Rib:https://www.poe2wiki.net/images/9/9d/Ancient_Rib_inventory_icon.png"
  "Gnawed_Collarbone:https://www.poe2wiki.net/images/b/bc/Gnawed_Collarbone_inventory_icon.png"
  "Gnawed_Jawbone:https://www.poe2wiki.net/images/a/a8/Gnawed_Jawbone_inventory_icon.png"
  "Gnawed_Rib:https://www.poe2wiki.net/images/8/81/Gnawed_Rib_inventory_icon.png"
  "Preserved_Collarbone:https://www.poe2wiki.net/images/7/7a/Preserved_Collarbone_inventory_icon.png"
  "Preserved_Jawbone:https://www.poe2wiki.net/images/4/47/Preserved_Jawbone_inventory_icon.png"
  "Preserved_Rib:https://www.poe2wiki.net/images/c/ce/Preserved_Rib_inventory_icon.png"
  "Preserved_Cranium:https://www.poe2wiki.net/images/6/69/Preserved_Cranium_inventory_icon.png"
  "Preserved_Vertebrae:https://www.poe2wiki.net/images/7/78/Preserved_Vertebrae_inventory_icon.png"
)

for item in "${urls[@]}"; do
  name="${item%%:*}"
  url="${item#*:}"
  status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
  if [ "$status" = "200" ]; then
    echo "✓ $name: $status"
  else
    echo "✗ $name: $status"
  fi
done
