"""Test bone icon URLs to find which ones work"""
import requests

bones = {
    'Ancient Collarbone': 'https://www.poe2wiki.net/images/2/29/Ancient_Collarbone_inventory_icon.png',
    'Ancient Jawbone': 'https://www.poe2wiki.net/images/7/79/Ancient_Jawbone_inventory_icon.png',
    'Ancient Rib': 'https://www.poe2wiki.net/images/9/9d/Ancient_Rib_inventory_icon.png',
    'Gnawed Collarbone': 'https://www.poe2wiki.net/images/b/bc/Gnawed_Collarbone_inventory_icon.png',
    'Gnawed Jawbone': 'https://www.poe2wiki.net/images/a/a8/Gnawed_Jawbone_inventory_icon.png',
    'Gnawed Rib': 'https://www.poe2wiki.net/images/8/81/Gnawed_Rib_inventory_icon.png',
    'Preserved Collarbone': 'https://www.poe2wiki.net/images/7/7a/Preserved_Collarbone_inventory_icon.png',
    'Preserved Jawbone': 'https://www.poe2wiki.net/images/4/47/Preserved_Jawbone_inventory_icon.png',
    'Preserved Rib': 'https://www.poe2wiki.net/images/c/ce/Preserved_Rib_inventory_icon.png',
    'Preserved Cranium': 'https://www.poe2wiki.net/images/6/69/Preserved_Cranium_inventory_icon.png',
    'Preserved Vertebrae': 'https://www.poe2wiki.net/images/7/78/Preserved_Vertebrae_inventory_icon.png',
}

print("Testing bone icon URLs...\n")
for name, url in bones.items():
    try:
        response = requests.head(url, allow_redirects=False, timeout=5)
        if response.status_code == 200:
            print(f"✓ {name}: {response.status_code}")
        else:
            print(f"✗ {name}: {response.status_code} - {url}")
    except Exception as e:
        print(f"✗ {name}: ERROR - {e}")
