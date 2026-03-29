# 🚢 Marine Engine AI Chatbot

An AI-powered chatbot that answers natural language questions about marine engine sensor data using **Groq AI (LLaMA)**, **DuckDB**, and **FastAPI**.

> Ask questions like:
> - *"What was the average RPM on 10 Feb 2026?"*
> - *"Show me port engine temperature on 13 Feb 2026"*
> - *"Which day had the highest starboard RPM?"*

---

## ⚡ Quick Start (ONE command)

### Windows
```bash
run.bat
```

### Mac / Linux
```bash
chmod +x run.sh
./run.sh
```

> These scripts automatically: create virtual environment → install all dependencies → start the chatbot.

**Before running**, open `src/templates/botmarch11.py` and set your Groq API key:
```python
GROQ_API_KEY = "gsk_XXXXXXXXXXXXXXXXXXXXXXXX"   # ← paste your key here
```
Get a free key at: https://console.groq.com

Then open your browser: **http://localhost:8000**

---

## ✅ Requirements

### System Requirements
| Requirement | Version |
|-------------|---------|
| Python | `3.9+` (tested on `3.12.3`) |
| pip | `23+` |
| OS | Windows 10/11, Ubuntu 20.04+, macOS 12+ |

### Python Package Requirements
| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | `>= 0.110.0` | Web framework / REST API |
| `uvicorn` | `>= 0.29.0` | ASGI server to run FastAPI |
| `duckdb` | `>= 0.10.0` | In-process SQL database engine |
| `groq` | `>= 0.5.0` | Groq AI API client (LLaMA models) |

### Standard Library Imports (no install needed)
```python
import os
import re
import json
import asyncio
```

### External API Requirements
| Service | Details |
|---------|---------|
| Groq API Key | Free tier — 100K tokens/day |
| Get key at | https://console.groq.com |
| SQL model | `llama-3.3-70b-versatile` |
| Answer model | `llama-3.1-8b-instant` |

---

## 📁 Project Structure

```
marine-engine-chatbot/
│
├── src/
│   └── templates/
│       ├── botmarch11.py          # ← Main FastAPI application (SOURCE CODE)
│       └── BELKO20260214.csv      # ← Marine engine dataset (place here)
│
├── run.bat                        # ← Double-click to run on Windows
├── run.sh                         # ← Run on Mac/Linux
├── requirements.txt               # Python dependencies
├── .gitignore                     # Git ignore rules
└── README.md                      # This file
```

---

## 🚀 Manual Installation (Alternative to run.bat)

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/marine-engine-chatbot.git
cd marine-engine-chatbot

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Set your Groq API key in src/templates/botmarch11.py

# 5. Run
cd src/templates
python botmarch11.py
```

### Expected Output on Startup
```
Cleaning CSV file...
Delimiter: ',', counts: {',': 13, ';': 0}
First line: DateAndTime,Time,EP_Cool_Temp_Value,...
Connecting to DuckDB...
Removed old dataset.db cache.
Dataset loaded!
Raw columns (14): ['DateAndTime', 'Time', ...]
Safe columns: ['DateAndTime', 'Time', ...]
✓ Final columns (14): ['DateAndTime', 'Time', ...]
✓ Total rows: 1451
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## ⚙️ Configuration

All configuration is at the top of `src/templates/botmarch11.py`:

```python
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
CSV_FILE     = os.path.join(BASE_DIR, "BELKO20260214.csv")  # raw dataset
CLEAN_CSV    = os.path.join(BASE_DIR, "BELKO_clean.csv")    # auto-generated
GROQ_API_KEY = "paste_your_groq_key_here"                   # ← SET THIS
```

| Variable | Description | Default |
|----------|-------------|---------|
| `CSV_FILE` | Path to raw input CSV | `BELKO20260214.csv` (same folder) |
| `CLEAN_CSV` | Auto-cleaned CSV (created on startup) | `BELKO_clean.csv` |
| `GROQ_API_KEY` | Your Groq API key | Must be set manually |
| `PORT` | Server port | `8000` |

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Server status + column list + row count |
| `GET` | `/chat?question=...` | Ask a natural language question |
| `GET` | `/schema` | View columns + sample rows |
| `GET` | `/debug` | Debug info: delimiter, raw vs safe columns |
| `GET` | `/docs` | Auto-generated FastAPI Swagger UI |

### Example Request
```
GET http://localhost:8000/chat?question=What was the average port RPM on 10 Feb 2026?
```

### Example Response
```json
{
  "question": "What was the average port RPM on 10 Feb 2026?",
  "answer": "The average Port engine RPM on 10 Feb 2026 was 62.45 RPM.",
  "sql_used": "SELECT ROUND(AVG(EP_RPM_Value), 2) FROM engine_data WHERE ...",
  "raw_data": [{"avg_rpm": 62.45}],
  "total_rows": 1
}
```

---

## 📊 Dataset Columns

**File:** `BELKO20260214.csv` | **Rows:** ~1,451 | **Date Range:** Feb 6 – Feb 21, 2026

| Column | Type | Description |
|--------|------|-------------|
| `DateAndTime` | VARCHAR | Date (two mixed formats) |
| `Time` | VARCHAR | Time of reading |
| `EP_Cool_Temp_Value` | DOUBLE | Port engine coolant temperature |
| `EP_Flow_Meter_Value` | DOUBLE | Port engine flow meter |
| `EP_Lube_Oil_Press_Value` | DOUBLE | Port engine lube oil pressure |
| `EP_RPM_Value` | DOUBLE | Port engine RPM |
| `AUX1_Flow_Meter_Value` | DOUBLE | Auxiliary 1 flow meter |
| `AUX2_Flow_Meter_Value` | DOUBLE | Auxiliary 2 flow meter |
| `Data_Capture_bit_Value` | BOOLEAN | Data capture flag |
| `STBD_Cool_Temp_Value` | DOUBLE | Starboard engine coolant temperature |
| `STBD_Flow_Meter_Value` | DOUBLE | Starboard engine flow meter |
| `STBD_Lube_Oil_Press_Value` | DOUBLE | Starboard engine lube oil pressure |
| `STBD_RPM_Value` | DOUBLE | Starboard engine RPM |
| `Scaled_value_from_S7_not_ok_Value` | BIGINT | Scaled S7 sensor value |

> `EP_` = Port engine &nbsp;|&nbsp; `STBD_` = Starboard engine

**Mixed date formats handled automatically:**
- Format A: `M/D/YYYY` → e.g. `2/7/2026`
- Format B: `DD-MM-YYYY` → e.g. `13-02-2026`

---

## 🛠 Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| AI - SQL Generation | Groq + LLaMA | `llama-3.3-70b-versatile` |
| AI - Answer Format | Groq + LLaMA | `llama-3.1-8b-instant` |
| AI Client | `groq` | `>= 0.5.0` |
| Database | DuckDB | `>= 0.10.0` |
| Web Framework | FastAPI | `>= 0.110.0` |
| ASGI Server | Uvicorn | `>= 0.29.0` |
| Language | Python | `3.9+` |

---

## ⚠️ Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `Invalid API Key` | Get a new key at https://console.groq.com |
| `Rate limit exceeded` | Groq free tier: 100K tokens/day. Wait or upgrade |
| `CSV not found` | Place `BELKO20260214.csv` in `src/templates/` |
| `Column not found` | Delete `dataset.db` and re-run |
| Port already in use | Change `port=8000` in `botmarch11.py` |

---

## 📄 License
MIT License — free to use and modify.
