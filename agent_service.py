import httpx
import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
import os
from dotenv import load_dotenv
import re

# 🔥 LOAD ENV
load_dotenv(override=True)
TINYFISH_API_KEY = os.getenv("TINYFISH_API_KEY")


# ================= CATEGORY =================
CATEGORY_SITES = {
    "electronics": ["tatacliq.com", "reliancedigital.in"],
    "grocery": ["bigbasket.com", "jiomart.com"],
    "fashion": ["ajio.com", "shopclues.com"],
    "beauty": ["purplle.com", "mamaearth.in"],
    "home": ["bajajelectronics.com", "giriasindia.com"]
}


# ================= MODEL =================
@dataclass
class ProductMonitor:
    name: str
    category: str
    sites: Optional[List[str]] = None


# ================= AGENT =================
class PriceGuardAgent:
    def __init__(self):
        if not TINYFISH_API_KEY:
            raise ValueError("❌ API key missing")

        self.api_key = TINYFISH_API_KEY.strip()
        self.base_url = "https://agent.tinyfish.ai/v1/automation/run-sse"

    # ================= GET SITES =================
    def get_sites(self, product: ProductMonitor) -> List[str]:
        return product.sites if product.sites else CATEGORY_SITES.get(product.category.lower(), [])

    # ================= EXTRACT SPECS =================
    def extract_specs(self, text: str) -> Dict:
        specs = {
            "ram": None,
            "storage": None,
            "camera": None,
            "display": None,
            "processor": None
        }

        if not text:
            return specs

        text = text.lower()

        if m := re.search(r'(\d+)\s?gb\s?ram', text):
            specs["ram"] = m.group(1) + "GB"

        if m := re.search(r'(\d+)\s?gb(?!\s?ram)', text):
            specs["storage"] = m.group(1) + "GB"

        if m := re.search(r'(\d+)\s?mp', text):
            specs["camera"] = m.group(1) + "MP"

        if m := re.search(r'(\d+\.?\d*)\s?inch', text):
            specs["display"] = m.group(1) + " inch"

        if "snapdragon" in text:
            specs["processor"] = "Snapdragon"
        elif "mediatek" in text:
            specs["processor"] = "MediaTek"
        elif "apple" in text:
            specs["processor"] = "Apple"

        return specs

    # ================= CLEAN PRICE =================
    def clean_price(self, raw):
        try:
            raw = str(raw)

            # Remove commas first
            raw = raw.replace(",", "")

            # Extract FIRST valid number (with optional decimal)
            match = re.search(r"\d+(?:\.\d+)?", raw)

            return float(match.group()) if match else 0.0

        except:
            return 0.0

    # ================= MAIN =================
    async def monitor_product(self, product: ProductMonitor) -> Dict:

        sites = self.get_sites(product)

        if not sites:
            return {"success": False, "error": "No sites found", "results": []}

        print("\n🔍 Monitoring:", product.name)
        print("🌐 Sites:", sites)

        # 🔥 STRONG PROMPT
        prompt = f"""
        STRICT:

        ONLY use these websites:
        {', '.join(sites)}

        DO NOT use any other sites.

        Search product: "{product.name}"

        Extract for each site:
        - site
        - price
        - specs

        OUTPUT STRICT JSON ARRAY ONLY:
        [
          {{"site":"...", "price":"...", "specs":"..."}}
        ]
        """

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(200.0, read=300.0)) as client:

                async with client.stream(
                    "POST",
                    self.base_url,
                    headers={
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream",
                        "User-Agent": "Mozilla/5.0"
                    },
                    json={"url": "https://google.com", "goal": prompt}
                ) as response:

                    if response.status_code != 200:
                        return {
                            "success": False,
                            "error": f"HTTP {response.status_code}",
                            "results": []
                        }

                    final_results = []

                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue

                        data = line[6:].strip()

                        if not data or "[DONE]" in data:
                            continue

                        try:
                            parsed = json.loads(data)

                            if parsed.get("type") == "COMPLETE":
                                result_block = parsed.get("result")

                                # 🔥 HANDLE STRING JSON (IMPORTANT FIX)
                                if isinstance(result_block, str):
                                    try:
                                        result_block = json.loads(result_block)
                                    except:
                                        continue

                                if isinstance(result_block, dict):
                                    final_results = result_block.get("result", [])

                                elif isinstance(result_block, list):
                                    final_results = result_block

                        except:
                            continue

        except Exception as e:
            return {"success": False, "error": str(e), "results": []}

        # ================= PROCESS =================
        results = []

        for item in final_results:
            if not isinstance(item, dict):
                continue

            raw_price = item.get("price", "0")

            results.append({
                "site": item.get("site", "unknown"),
                "price": self.clean_price(raw_price),
                "raw_price": raw_price,
                "specs": item.get("specs", ""),
                **self.extract_specs(item.get("specs", ""))
            })

        # 🔥 NO FAKE FALLBACK → RETURN EMPTY
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "product": product.name,
            "category": product.category,
            "results": results
        }


# ================= INSTANCE =================
agent = PriceGuardAgent()

print("✅ Agent Ready (FINAL PRO VERSION)")