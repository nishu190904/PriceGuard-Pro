import httpx
import asyncio
import json
import os
from dotenv import load_dotenv

# 🔥 Load env properly
load_dotenv(override=True)
api_key = os.getenv("TINYFISH_API_KEY")


# ✅ CATEGORY → SITES
CATEGORY_SITES = {
    "1": ("electronics", ["tatacliq.com", "reliancedigital.in"]),
    "2": ("grocery", ["bigbasket.com", "jiomart.com"]),
    "3": ("fashion", ["ajio.com", "shopclues.com"]),
    "4": ("beauty", ["purplle.com", "mamaearth.in"]),
    "5": ("home", ["bajajelectronics.com", "giriasindia.com"])
}


async def test():

    if not api_key:
        print("❌ API key not found")
        return

    print("🔑 API Key Loaded: ✅\n")

    # ================= USER INPUT =================
    print("📂 Select Category:")
    print("1 → Electronics")
    print("2 → Grocery")
    print("3 → Fashion")
    print("4 → Beauty")
    print("5 → Home Appliances")

    choice = input("\nEnter category number: ").strip()

    if choice not in CATEGORY_SITES:
        print("❌ Invalid category")
        return

    category, sites = CATEGORY_SITES[choice]

    product = input("📦 Enter product name: ").strip()

    override = input("✏️ Override sites? (yes/no): ").strip().lower()

    if override == "yes":
        custom_sites = input("Enter sites (comma separated): ")
        sites = [s.strip() for s in custom_sites.split(",") if s.strip()]

    print("\n🚀 Running TinyFish...")
    print(f"📦 Product: {product}")
    print(f"📂 Category: {category}")
    print(f"🌐 Sites: {sites}\n")

    # ================= STRONG PROMPT =================
    prompt = f"""
    STRICT INSTRUCTIONS:

    1. ONLY use these websites:
       {', '.join(sites)}

    2. DO NOT use Amazon, Flipkart or any other site.

    3. Search for product: "{product}"

    4. For EACH website:
       - Open the website
       - Search the product
       - Open the most relevant result
       - Extract:
            • site name
            • price (as shown, keep ₹ if present)
            • key specifications

    5. IMPORTANT:
       - Ensure correct product match
       - Do NOT skip any website
       - If not found → write "Not available"

    6. OUTPUT FORMAT (STRICT JSON ONLY):

    [
      {{
        "site": "example.com",
        "price": "₹1234",
        "specs": "details here"
      }}
    ]

    NO explanation. ONLY JSON.
    """

    async with httpx.AsyncClient(timeout=httpx.Timeout(200.0, read=300.0)) as client:
        try:
            async with client.stream(
                "POST",
                "https://agent.tinyfish.ai/v1/automation/run-sse",
                headers={
                    "X-API-Key": api_key.strip(),
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                    "User-Agent": "Mozilla/5.0"
                },
                json={
                    "url": "https://www.google.com",
                    "goal": prompt
                }
            ) as response:

                print(f"✅ Status: {response.status_code}\n")

                if response.status_code == 403:
                    print("❌ 403 Forbidden → API issue")
                    return

                final_results = []

                print("⏳ Processing...\n")

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    data = line[6:].strip()

                    if not data:
                        continue

                    if "[DONE]" in data:
                        break

                    try:
                        parsed = json.loads(data)

                        # 🎯 FINAL RESULT
                        if parsed.get("type") == "COMPLETE":
                            result_block = parsed.get("result", {})

                            if isinstance(result_block, dict):
                                final_results = result_block.get("result", [])
                            elif isinstance(result_block, list):
                                final_results = result_block

                    except json.JSONDecodeError:
                        continue

                print("\n🎉 RESULTS\n")

                if final_results:
                    for item in final_results:
                        print(f"🌐 {item.get('site')}")
                        print(f"💵 {item.get('price')}")
                        print(f"📋 {item.get('specs')}")
                        print("-" * 40)
                else:
                    print("⚠️ No structured results found")

        except Exception as e:
            print(f"❌ ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(test())