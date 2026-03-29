import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="🚀 PriceGuard Pro", layout="wide")

API_BASE = "http://127.0.0.1:8000"

CATEGORY_SITES = {
    "electronics": ["tatacliq.com", "reliancedigital.in"],
    "grocery": ["bigbasket.com", "jiomart.com"],
    "fashion": ["ajio.com", "shopclues.com"],
    "beauty": ["purplle.com", "mamaearth.in"],
    "home": ["bajajelectronics.com", "giriasindia.com"]
}

progress_bar = st.empty()


# ================= SAFE API =================
def safe_request(method, endpoint, data=None, timeout=600):
    try:
        url = f"{API_BASE}{endpoint}"

        resp = requests.request(
            method,
            url,
            json=data if data else None,
            timeout=timeout
        )

        resp.raise_for_status()
        return resp.json()

    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "🚫 Backend not running"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "⏳ AI timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ================= SAFE PRICE =================
def safe_price(value):
    try:
        return float(value)
    except:
        return None


# ================= UI =================
st.title("💰 PriceGuard Pro")
st.caption("🤖 AI-powered multi-site price comparison")

# Backend check
health = safe_request("GET", "/")

if health.get("status"):
    st.sidebar.success("✅ Backend Connected")
else:
    st.sidebar.error("❌ Backend Not Connected")

tab1, tab2 = st.tabs(["🚀 Compare Product", "📈 History"])


# ================= HISTORY =================
with tab2:
    product = st.text_input("Search product history", "iPhone")

    if st.button("🔍 Load History"):
        history = safe_request("GET", f"/history/{product}")

        if history:
            st.dataframe(pd.DataFrame(history))
        else:
            st.warning("No history found")


# ================= MAIN =================
with tab1:

    with st.form("form"):

        category = st.selectbox("Select Category", list(CATEGORY_SITES.keys()))
        name = st.text_input("Product Name", "iPhone 15")

        auto_sites = CATEGORY_SITES[category]

        st.text_input("Selected Sites", value=", ".join(auto_sites), disabled=True)

        custom = st.text_input("Override sites (optional)")

        submit = st.form_submit_button("🔍 Compare Prices")

        if submit:

            sites = (
                [s.strip() for s in custom.split(",") if s.strip()]
                if custom else auto_sites
            )

            if not sites:
                st.warning("No sites selected")
                st.stop()

            progress_bar.progress(20)

            with st.spinner("Comparing prices across sites..."):
                result = safe_request("POST", "/monitor", {
                    "name": name,
                    "category": category,
                    "sites": sites
                })

            progress_bar.progress(100)

            if not result.get("success"):
                st.error(result.get("error"))
                st.stop()

            results = result.get("results", [])

            if not results:
                st.warning("No results found")
                st.stop()

            df = pd.DataFrame(results)

            # Remove unwanted columns
            df = df.drop(columns=["raw_price"], errors="ignore")

            # ✅ SAFE price conversion
            df["price"] = df["price"].apply(safe_price)

            # Remove invalid prices
            df = df[df["price"].notna()]

            # Sort
            df = df.sort_values("price")

            # Format price properly
            df["price"] = df["price"].apply(
                lambda x: f"₹{x:,.2f}"
            )

            # Detect spec columns dynamically
            spec_columns = [c for c in df.columns if c not in ["site", "price", "specs"]]

            has_specs = any(df[c].notna().any() for c in spec_columns)

            # ================= SHOW =================
            if has_specs:
                st.dataframe(df, use_container_width=True)
            else:
                st.subheader("💡 Results")

                for item in results:
                    price_val = safe_price(item.get("price"))

                    st.markdown(f"""
                    ### 🌐 {item.get("site")}
                    💰 **Price:** {f"₹{price_val:,.2f}" if price_val else "N/A"}  
                    📋 {item.get("specs", "No specs available")}
                    ---
                    """)

            with st.expander("Raw JSON"):
                st.json(result)