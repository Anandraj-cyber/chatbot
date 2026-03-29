from imports import *
import hashlib
import torch
from transformers import pipeline as hf_pipeline
from nlppipeline import run_nlp_pipeline, NLPResult

# ── Config ─────────────────────────────────────────────────────────────────
CSV_FILE   = "testing.csv"
CLEAN_CSV  = "BELKO_clean.csv"
DUCKDB_FILE = "dataset.db"
TABLE_NAME  = "engine_data"

MODEL_PATH               = "/home/ved11/evito-sapi-restp-tools/models/tinyllama"
NLP_CONFIDENCE_THRESHOLD = 0.70

# ── Health intent keywords ─────────────────────────────────────────────────
HEALTH_KEYWORDS = [
    "health", "healthy", "status", "condition", "safe",
    "warning", "critical", "danger", "alert", "diagnose",
    "diagnosis", "report", "how is", "how are", "is it",
    "are they", "overall", "summary", "performance",
    "running well", "any issue", "any problem", "any fault",
    "any alarm", "engine check", "engine report", "rpm health",
    "temperature health", "pressure health", "engine status",
    "engine condition", "is engine", "check engine"
]

# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(title="Engine Data AI Chatbot — SLM + NLP (No API Key)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ── Step 1: Clean CSV ─────────────────────────────────────────────────────
print("Cleaning CSV file...")
with open(CSV_FILE, 'r', encoding='utf-8-sig', newline='') as f:
    raw = f.read()

raw = raw.replace('\r\n', '\n').replace('\r', '\n')

with open(CLEAN_CSV, 'w', encoding='utf-8', newline='\n') as f:
    f.write(raw)

first_line = raw.split('\n')[0]
delimiters = {',': first_line.count(','), ';': first_line.count(';'), '\t': first_line.count('\t')}
best_delim = max(delimiters, key=delimiters.get)
print(f"Delimiter: {repr(best_delim)}")
print(f"First line: {first_line[:100]}")

# ── Step 2: Load into DuckDB ───────────────────────────────────────────────
print("Connecting to DuckDB...")
con = duckdb.connect(DUCKDB_FILE)

con.execute(f"""
CREATE OR REPLACE TABLE {TABLE_NAME} AS
SELECT * FROM read_csv_auto('{CLEAN_CSV}',
    header=True,
    delim='{best_delim}',
    ignore_errors=True
)
""")
print("Dataset loaded!")

raw_columns   = con.execute(f"DESCRIBE {TABLE_NAME}").fetchall()
raw_col_names = [c[0] for c in raw_columns]
print(f"Raw columns ({len(raw_col_names)}): {raw_col_names}")

# ── Step 3: Sanitize column names ─────────────────────────────────────────
def sanitize(name: str) -> str:
    name = name.strip().lstrip('\ufeff')
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name).strip('_')
    return name

safe_map    = {orig: sanitize(orig) for orig in raw_col_names}
rename_expr = ", ".join(f'"{orig}" AS {safe}' for orig, safe in safe_map.items())
con.execute(f"CREATE OR REPLACE TABLE {TABLE_NAME} AS SELECT {rename_expr} FROM {TABLE_NAME}")

safe_columns     = list(safe_map.values())
safe_sample_rows = con.execute(f"SELECT * FROM {TABLE_NAME} LIMIT 3").fetchall()
total_rows       = con.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()[0]

print(f"✓ Final columns ({len(safe_columns)}): {safe_columns}")
print(f"✓ Total rows: {total_rows}")

# ── Load TinyLlama once at startup ─────────────────────────────────────────
print("Loading TinyLlama from local path (first load ~40sec)...")
try:
    slm_pipe = hf_pipeline(
        "text-generation",
        model=MODEL_PATH,
        device="cpu",
        dtype=torch.float32
    )
    SLM_AVAILABLE = True
    print("✓ TinyLlama loaded successfully!")
except Exception as e:
    slm_pipe      = None
    SLM_AVAILABLE = False
    print(f"⚠ TinyLlama failed to load: {e}")

# ── Column helpers ─────────────────────────────────────────────────────────
def get_safe_columns() -> list:
    try:
        return [c[0] for c in con.execute(f"DESCRIBE {TABLE_NAME}").fetchall()]
    except Exception:
        return safe_columns

def get_total_rows() -> int:
    try:
        return con.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()[0]
    except Exception:
        return 0

# ── TinyLlama caller — token safe ─────────────────────────────────────────
def slm_chat(system_prompt: str, user_message: str, max_tokens: int = 300) -> str:
    if not SLM_AVAILABLE:
        raise RuntimeError("TinyLlama model not loaded")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_message}
    ]
    prompt = slm_pipe.tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    tokens = slm_pipe.tokenizer.encode(prompt)
    if len(tokens) > 1500:
        tokens = tokens[:1500]
        prompt = slm_pipe.tokenizer.decode(tokens)
        print(f"[HEALTH] Prompt trimmed to 1500 tokens")
    result = slm_pipe(
        prompt,
        max_new_tokens=max_tokens,
        do_sample=False,
        repetition_penalty=1.1,
        pad_token_id=slm_pipe.tokenizer.eos_token_id
    )
    return result[0]["generated_text"][len(prompt):].strip()

# ── Health intent detector ─────────────────────────────────────────────────
def is_health_query(question: str) -> bool:
    low = question.lower()
    return any(kw in low for kw in HEALTH_KEYWORDS)

# ── Fetch engine snapshot for health ──────────────────────────────────────
def fetch_health_snapshot() -> dict:
    cols        = get_safe_columns()
    latest_rows = con.execute(
        f"SELECT * FROM {TABLE_NAME} ORDER BY DateAndTime DESC LIMIT 10"
    ).fetchall()
    latest = [dict(zip(cols, r)) for r in latest_rows]
    stats  = {}
    for col in cols:
        try:
            row = con.execute(f"""
                SELECT
                    ROUND(AVG(CAST({col} AS DOUBLE)), 2),
                    ROUND(MIN(CAST({col} AS DOUBLE)), 2),
                    ROUND(MAX(CAST({col} AS DOUBLE)), 2),
                    ROUND(STDDEV(CAST({col} AS DOUBLE)), 2)
                FROM {TABLE_NAME}
            """).fetchone()
            if row and row[0] is not None:
                stats[col] = {
                    "avg": row[0], "min": row[1],
                    "max": row[2], "stddev": row[3]
                }
        except Exception:
            pass
    return {
        "latest_records": latest,
        "column_stats":   stats,
        "total_rows":     get_total_rows()
    }

# ── Health engine — TinyLlama driven ──────────────────────────────────────
def run_health_engine(question: str) -> dict:
    print(f"[HEALTH] Running TinyLlama analysis for: {question}")
    snapshot    = fetch_health_snapshot()
    stats_items = list(snapshot["column_stats"].items())[:10]
    stats_text  = "\n".join(
        f"  {col}: avg={v['avg']}, min={v['min']}, max={v['max']}, stddev={v['stddev']}"
        for col, v in stats_items
    )
    latest_text = json.dumps(snapshot["latest_records"][:3], default=str)[:800]

    system_prompt = f"""You are a marine engine health analyst AI.
Total records: {snapshot['total_rows']}

Key statistics (avg/min/max/stddev):
{stats_text}

Latest readings:
{latest_text}

RULES:
- WARNING if latest value deviates more than 2x stddev from avg
- CRITICAL if latest value deviates more than 3x stddev from avg
- GOOD if within normal range
- EP_ = Port engine | STBD_ = Starboard engine
- Base ALL judgments on actual data only

RESPOND IN THIS EXACT FORMAT:
OVERALL STATUS: [🟢 Good / 🟡 Warning / 🔴 Critical]

SUMMARY:
[2 sentences about overall engine health]

DETAILED REPORT:
- RPM: [🟢/🟡/🔴] — [latest value] vs normal [min-max], [reason]
- Temperature: [🟢/🟡/🔴] — [latest value°C] vs normal, [reason]
- Pressure: [🟢/🟡/🔴] — [latest value bar] vs normal, [reason]
- Coolant: [🟢/🟡/🔴] — [latest value] vs normal, [reason]

RECOMMENDATION:
[1 sentence action or "No action needed"]"""

    try:
        answer = slm_chat(
            system_prompt=system_prompt,
            user_message=f"Analyze engine health for: '{question}'",
            max_tokens=300
        )
        return {
            "question":   question,
            "answer":     answer,
            "raw_data":   snapshot["latest_records"][:3],
            "total_rows": snapshot["total_rows"],
            "source":     "tinyllama_health",
            "note":       "Health analysis uses local TinyLlama AI (~90 sec)"
        }
    except Exception as e:
        return {
            "question": question,
            "answer":   f"Health analysis failed: {str(e)}",
            "error":    str(e),
            "source":   "health_error"
        }

# ── NLP execute + format ───────────────────────────────────────────────────
def execute_nlp(question: str, sql: str) -> dict:
    sql_dynamic = sql.replace("FROM engine_data", f"FROM {TABLE_NAME}")
    result      = con.execute(sql_dynamic).fetchall()
    desc        = con.execute(sql_dynamic).description
    col_names   = [d[0] for d in desc]
    structured  = [dict(zip(col_names, r)) for r in result]
    count       = len(structured)
    if count == 0:
        answer = "No data found for that query."
    elif count == 1 and len(structured[0]) == 1:
        key, val = list(structured[0].items())[0]
        answer = f"The result is {val}."
    else:
        answer = f"Found {count} record(s) matching your query."
    return {
        "question":   question,
        "answer":     answer,
        "sql_used":   sql_dynamic,
        "raw_data":   structured[:20],
        "total_rows": count,
        "source":     "spacy_nlp"
    }

# ── NLP fallback ───────────────────────────────────────────────────────────
def nlp_fallback(question: str) -> dict:
    total = get_total_rows()
    return {
        "question": question,
        "answer": (
            f"I couldn't understand your query. "
            f"I have {total} engine records. "
            f"Try asking about RPM, temperature, pressure, flow meter, "
            f"date ranges, latest records, or engine health."
        ),
        "raw_data":   [],
        "total_rows": 0,
        "source":     "nlp_fallback"
    }

# ── Query cache ────────────────────────────────────────────────────────────
query_cache: dict = {}

# ── Master handler ─────────────────────────────────────────────────────────
def ask_dataset(question: str) -> dict:
    cache_key = hashlib.md5(question.lower().strip().encode()).hexdigest()
    if cache_key in query_cache:
        print(f"[CACHE HIT] {question}")
        cached = query_cache[cache_key].copy()
        cached["source"] = cached.get("source", "") + " (cached)"
        return cached

    cols = get_safe_columns()

    # Step 1: Health query → TinyLlama
    if is_health_query(question):
        print(f"[HEALTH INTENT] {question}")
        result = run_health_engine(question)
        query_cache[cache_key] = result
        return result

    # Step 2: Data query → spaCy NLP
    nlp_result: NLPResult = run_nlp_pipeline(question, cols)
    print(f"[spaCy NLP] intent={nlp_result.intent} confidence={nlp_result.confidence} sql={nlp_result.sql[:60] if nlp_result.sql else 'none'}")

    if nlp_result.sql and nlp_result.confidence >= NLP_CONFIDENCE_THRESHOLD:
        try:
            result = execute_nlp(question, nlp_result.sql)
            query_cache[cache_key] = result
            return result
        except Exception as e:
            print(f"[NLP EXEC ERROR] {e}")

    # Step 3: Fallback
    print(f"[FALLBACK] confidence too low: {nlp_result.confidence}")
    return nlp_fallback(question)

# ── Routes ─────────────────────────────────────────────────────────────────
@app.get("/")
def home():
    return {
        "message":       "Engine AI Chatbot — SLM + NLP (No API Key)",
        "slm_available": SLM_AVAILABLE,
        "columns":       safe_columns,
        "total_rows":    total_rows,
        "cache_size":    len(query_cache)
    }

@app.get("/chat")
def chat(question: str = Query(...)):
    return ask_dataset(question)

@app.get("/health")
def health_report():
    return run_health_engine("Give me a complete engine health report")

@app.get("/schema")
def schema():
    return {
        "columns":     safe_columns,
        "sample_rows": [dict(zip(safe_columns, row)) for row in safe_sample_rows]
    }

@app.get("/debug")
def debug():
    return {
        "delimiter":     repr(best_delim),
        "raw_columns":   raw_col_names,
        "safe_columns":  safe_columns,
        "total_rows":    total_rows,
        "slm_available": SLM_AVAILABLE,
        "nlp_engine":    "spaCy blank model + Matcher",
        "cache_size":    len(query_cache),
        "sample":        [dict(zip(safe_columns, row)) for row in safe_sample_rows]
    }

@app.delete("/cache")
def clear_cache():
    query_cache.clear()
    return {"message": "Cache cleared"}

# ── Server ─────────────────────────────────────────────────────────────────
async def run_servers():
    config_v4 = uvicorn.Config(app, host="0.0.0.0", port=8000)
    config_v6 = uvicorn.Config(app, host="::", port=8000)
    server_v4 = uvicorn.Server(config_v4)
    server_v6 = uvicorn.Server(config_v6)
    await asyncio.gather(server_v4.serve(), server_v6.serve())

if __name__ == "__main__":
    asyncio.run(run_servers())