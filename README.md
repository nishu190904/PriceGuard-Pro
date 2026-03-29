# 🚀 PriceGuard Pro

An AI-powered multi-site price comparison system that automatically
searches products across multiple e-commerce websites, extracts prices
and specifications, and displays structured results with history
tracking.

\---

## 📌 Features

* 🔍 Multi-site product search (category-based)
* 💰 Real-time price extraction
* 📊 Dynamic specification extraction
* 📈 Price history tracking (SQLite)
* ⚡ FastAPI backend
* 🖥️ Streamlit dashboard
* 🤖 AI-powered web automation using TinyFish

\---

## 🧠 Problem Statement

Manual price comparison across websites is time-consuming and
inefficient. Users often miss better deals.

\---

## 💡 Solution

PriceGuard Pro automates: - Product search - Price extraction -
Multi-site comparison - History tracking

\---

## 🏗️ Architecture

User → Streamlit → FastAPI → TinyFish → Websites → Database → UI

\---

## ⚙️ Tech Stack

* Python 3.11
* FastAPI
* Streamlit
* TinyFish API
* SQLite

\---

## 📂 Project Structure

PriceGuard/ - main.py - agent\_service.py - dashboard.py -
test\_tinyfish.py - requirements.txt - README.md

\---

## 🐍 Setup Guide

### 1\. Install Python 3.11

https://www.python.org/downloads/

### 2\. Clone Repo

git clone https://github.com/yourusername/PriceGuard-Pro.git cd
PriceGuard-Pro

### 3\. Create Virtual Environment

python -m venv venv

### 4\. Activate

Windows: venv`\\Scripts`{=tex}`\\activate`{=tex}

Mac/Linux: source venv/bin/activate

### 5\. Install Dependencies

pip install -r requirements.txt

### 6\. Add .env

TINYFISH\_API\_KEY=your\_api\_key\_here

### 7\. Run Backend

uvicorn main:app --reload

### 8\. Run Frontend

streamlit run dashboard.py

\---

## 📊 API Endpoints

GET / POST /monitor GET /history/{product}

\---

## 🔮 Future Scope

* Price alerts
* Graphs
* Full automation
* SaaS deployment

\---

## 👨‍💻 Author

Nishant Kumar Roy

Daipayan Biswas

Ranit Das

Subhojit Ghosh

\---

## ⭐ Support

Star ⭐ this repo if you like it!

