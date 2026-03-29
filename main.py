from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
from pydantic import BaseModel
from typing import List, Optional
from agent_service import agent, ProductMonitor
import traceback
import re

# ================= INIT APP =================
app = FastAPI(title="PriceGuard Pro API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# ================= DB =================
DB_NAME = "price_history.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT,
        category TEXT,
        site TEXT,
        price REAL,
        timestamp TEXT,
        data TEXT
    )
    """)
    conn.commit()
    conn.close()
    print("✅ Database initialized")


@app.on_event("startup")
def startup():
    init_db()


# ================= MODEL =================
class Product(BaseModel):
    name: str
    category: str
    sites: Optional[List[str]] = None



# ================= UTIL =================
def clean_price(price):
    try:
        raw = str(price)

        # Remove commas
        raw = raw.replace(",", "")

        # Extract first valid number (with optional decimal)
        match = re.search(r"\d+(?:\.\d+)?", raw)

        return float(match.group()) if match else 0.0

    except:
        return 0.0

# ================= MONITOR =================
@app.post("/monitor")
async def monitor_single(product: Product):
    try:
        print("\n🔍 REQUEST ----------------")
        print(product.dict())

        # 🚫 VALIDATION
        if not product.name.strip():
            return {"success": False, "error": "Product name is empty", "results": []}

        monitor = ProductMonitor(
            name=product.name,
            category=product.category,
            sites=product.sites
        )

        result = await agent.monitor_product(monitor)

        # ❌ Agent failed
        if not result.get("success"):
            return result

        conn = get_db()

        for item in result.get("results", []):
            try:
                conn.execute(
                    """
                    INSERT INTO prices (product, category, site, price, timestamp, data)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        result.get("product"),
                        result.get("category"),
                        item.get("site", "unknown"),
                        clean_price(item.get("price")),
                        result.get("timestamp"),
                        json.dumps(item)
                    )
                )
            except Exception as e:
                print("⚠️ DB insert error:", e)

        conn.commit()
        conn.close()

        print("💾 Data saved")

        return result

    except Exception as e:
        print("🚨 ERROR:\n", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ================= ROOT =================
@app.get("/")
def root():
    return {
        "status": True,
        "message": "🚀 PriceGuard Pro API running"
    }


# ================= HISTORY =================
@app.get("/history/{product}")
def history(product: str):
    try:
        conn = get_db()

        rows = conn.execute(
            """
            SELECT product, category, site, price, timestamp
            FROM prices
            WHERE product LIKE ?
            ORDER BY timestamp DESC
            """,
            (f"%{product}%",)
        ).fetchall()

        conn.close()

        return [
            {
                "product": r["product"],
                "category": r["category"],
                "site": r["site"],
                "price": r["price"],
                "timestamp": r["timestamp"]
            }
            for r in rows
        ]

    except Exception as e:
        print("❌ History Error:", e)
        return []


print("✅ FastAPI Backend Ready (FINAL)")