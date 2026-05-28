
import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8000/api/v1"

# ID from the user's error message
PRODUCT_ID = "b38b07f2-22a8-4267-9085-9a47ed15e6b0" 
# Or use a generic one if that one doesn't exist, but trying to query it first is good.

async def test_update():
    async with aiohttp.ClientSession() as session:
        # 1. First, try to get the product to ensure it exists and see its data
        print(f"Fetching product {PRODUCT_ID}...")
        async with session.get(f"{BASE_URL}/products/{PRODUCT_ID}") as resp:
            if resp.status != 200:
                print(f"Failed to get product: {resp.status}")
                text = await resp.text()
                print(text)
                return
            product = await resp.json()
            print("Current Product Data:", json.dumps(product, indent=2, ensure_ascii=False))

        # 2. Try to update with the payload we suspect is failing
        # Based on Catalog.vue:
        # payload = {
        #   name: productForm.value.name,
        #   base_price: productForm.value.base_price,
        #   category_id: productForm.value.category_id || null
        # }
        
        payload = {
            "name": product["name"], # Keep existing name
            "base_price": product["base_price"],
            "category_id": None # Test setting null
        }
        
        print("\nSending Payload (Null Category):")
        print(json.dumps(payload, indent=2, ensure_ascii=False))

        async with session.put(f"{BASE_URL}/products/{PRODUCT_ID}", json=payload) as resp:
            print(f"\nUpdate Status: {resp.status}")
            text = await resp.text()
            print("Response:", text)

        # 3. Try with an empty string for category_id just in case
        payload_empty_str = {
             "name": product["name"],
             "base_price": product["base_price"],
             "category_id": "" 
        }
        print("\nSending Payload (Empty String Category):")
        print(json.dumps(payload_empty_str, indent=2, ensure_ascii=False))
        
        async with session.put(f"{BASE_URL}/products/{PRODUCT_ID}", json=payload_empty_str) as resp:
            print(f"\nUpdate Status (Empty String): {resp.status}")
            text = await resp.text()
            print("Response:", text)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_update())
