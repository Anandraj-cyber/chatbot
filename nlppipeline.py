# nlppipeline.py — spaCy Rule-Based NLP Pipeline
# Uses spaCy blank model + Matcher — NO model download needed
# Pure AI-based intent detection using linguistic pattern matching

import re
import spacy
from spacy.matcher import Matcher
from dataclasses import dataclass, field

# ── Load blank spaCy model — no download needed ───────────────────────────
nlp = spacy.blank("en")

# ── Typo correction ────────────────────────────────────────────────────────
TYPO_MAP = {
    "averge": "average", "avrage": "average", "avarage": "average",
    "maximun": "maximum", "maxium": "maximum",
    "minimun": "minimum", "minmum": "minimum",
    "temprature": "temperature", "temparature": "temperature",
    "presure": "pressure", "pressue": "pressure",
    "coolan": "coolant", "coolent": "coolant",
    "engien": "engine", "enigne": "engine",
    "starbaord": "starboard", "starborad": "starboard",
    "anoamly": "anomaly", "anomlay": "anomaly",
    "recnt": "recent", "frist": "first",
    "shwo": "show", "hwo": "how",
    "datas": "data", "recods": "records", "recorde": "records",
    "totel": "total", "totla": "total", "totoal": "total",
    "engin": "engine", "egine": "engine",
    "curent": "current", "currnt": "current",
    "lastest": "latest", "lates": "latest",
    "enteries": "entries", "entrys": "entries",
    "hieghest": "highest", "higest": "highest",
    "lowset": "lowest", "lowst": "lowest",
    "greaest": "greatest", "greates": "greatest",
}

# ── METRIC_MAP — maps keywords to column name fragments ───────────────────
METRIC_MAP = {
    "rpm":         "RPM",
    "speed":       "RPM",
    "revolution":  "RPM",
    "temperature": "Cool_Temp",
    "temp":        "Cool_Temp",
    "coolant":     "Cool_Temp",
    "cool":        "Cool_Temp",
    "cooling":     "Cool_Temp",
    "pressure":    "Lube_Oil_Press",
    "lube":        "Lube_Oil_Press",
    "oil":         "Lube_Oil_Press",
    "lubrication": "Lube_Oil_Press",
    "flow":        "Flow_Meter",
    "fuel":        "Flow_Meter",
    "meter":       "Flow_Meter",
}

MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2,
    "march": 3,   "mar": 3, "april": 4,    "apr": 4,
    "may": 5,     "june": 6,"jun": 6,      "july": 7,
    "jul": 7,     "august": 8,"aug": 8,    "september": 9,
    "sep": 9,     "october": 10,"oct": 10, "november": 11,
    "nov": 11,    "december": 12,"dec": 12,
}

WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "hundred": 100,
}

PORT_WORDS  = {"port", "ep", "left"}
STBD_WORDS  = {"starboard", "stbd", "right"}

# ── Build spaCy Matcher with intent patterns ───────────────────────────────
matcher = Matcher(nlp.vocab)

matcher.add("AVERAGE", [
    [{"LOWER": "average"}], [{"LOWER": "avg"}], [{"LOWER": "mean"}],
    [{"LOWER": "typical"}], [{"LOWER": "normally"}], [{"LOWER": "generally"}],
    [{"LOWER": "what"}, {"LOWER": "is"}, {"LOWER": "the"}, {"LOWER": "average"}],
])

matcher.add("MAXIMUM", [
    [{"LOWER": "maximum"}], [{"LOWER": "max"}], [{"LOWER": "highest"}],
    [{"LOWER": "peak"}], [{"LOWER": "greatest"}], [{"LOWER": "largest"}],
    [{"LOWER": "biggest"}], [{"LOWER": "top"}, {"LOWER": "value"}],
    [{"LOWER": "what"}, {"LOWER": "is"}, {"LOWER": "the"}, {"LOWER": "highest"}],
    [{"LOWER": "what"}, {"LOWER": "is"}, {"LOWER": "the"}, {"LOWER": "maximum"}],
    [{"LOWER": "what"}, {"LOWER": "is"}, {"LOWER": "the"}, {"LOWER": "max"}],
    [{"LOWER": "what"}, {"LOWER": "is"}, {"LOWER": "highest"}],
    [{"LOWER": "what"}, {"LOWER": "is"}, {"LOWER": "max"}],
])

matcher.add("MINIMUM", [
    [{"LOWER": "minimum"}], [{"LOWER": "min"}], [{"LOWER": "lowest"}],
    [{"LOWER": "least"}], [{"LOWER": "smallest"}],
    [{"LOWER": "bottom"}, {"LOWER": "value"}],
    [{"LOWER": "what"}, {"LOWER": "is"}, {"LOWER": "the"}, {"LOWER": "lowest"}],
    [{"LOWER": "what"}, {"LOWER": "is"}, {"LOWER": "the"}, {"LOWER": "minimum"}],
    [{"LOWER": "what"}, {"LOWER": "is"}, {"LOWER": "lowest"}],
])

matcher.add("COUNT", [
    [{"LOWER": "count"}], [{"LOWER": "total"}], [{"LOWER": "size"}],
    [{"LOWER": "how"}, {"LOWER": "many"}],
    [{"LOWER": "number"}, {"LOWER": "of"}],
    [{"LOWER": "how"}, {"LOWER": "much"}, {"LOWER": "data"}],
])

matcher.add("LATEST", [
    [{"LOWER": "latest"}], [{"LOWER": "recent"}], [{"LOWER": "last"}],
    [{"LOWER": "newest"}], [{"LOWER": "current"}], [{"LOWER": "today"}],
    [{"LOWER": "first"}], [{"LOWER": "records"}], [{"LOWER": "rows"}],
    [{"LOWER": "data"}], [{"LOWER": "entries"}], [{"LOWER": "entry"}],
    [{"LOWER": "recent"}, {"LOWER": "records"}],
    [{"LOWER": "last"}, {"IS_DIGIT": True}, {"LOWER": "records"}],
    [{"LOWER": "last"}, {"IS_DIGIT": True}, {"LOWER": "entries"}],
    [{"LOWER": "first"}, {"IS_DIGIT": True}, {"LOWER": "records"}],
    [{"LOWER": "show"}, {"LOWER": "records"}],
    [{"LOWER": "show"}, {"LOWER": "data"}],
    [{"LOWER": "show"}, {"LOWER": "entries"}],
])

matcher.add("LIST", [
    [{"LOWER": "list"}], [{"LOWER": "show"}], [{"LOWER": "display"}],
    [{"LOWER": "fetch"}], [{"LOWER": "find"}], [{"LOWER": "get"}],
    [{"LOWER": "see"}], [{"LOWER": "retrieve"}],
    [{"LOWER": "give"}, {"LOWER": "me"}],
    [{"LOWER": "tell"}, {"LOWER": "me"}],
    [{"LOWER": "what"}, {"LOWER": "are"}],
])

matcher.add("ANOMALY", [
    [{"LOWER": "anomaly"}], [{"LOWER": "unusual"}], [{"LOWER": "spike"}],
    [{"LOWER": "abnormal"}], [{"LOWER": "fault"}], [{"LOWER": "alarm"}],
    [{"LOWER": "strange"}], [{"LOWER": "weird"}], [{"LOWER": "outlier"}],
    [{"LOWER": "any"}, {"LOWER": "issue"}],
    [{"LOWER": "any"}, {"LOWER": "problem"}],
    [{"LOWER": "any"}, {"LOWER": "error"}],
])

matcher.add("DATE_GROUP", [
    [{"LOWER": "which"}, {"LOWER": "date"}],
    [{"LOWER": "what"}, {"LOWER": "date"}],
    [{"LOWER": "date"}, {"LOWER": "wise"}],
    [{"LOWER": "per"}, {"LOWER": "date"}],
    [{"LOWER": "most"}, {"LOWER": "records"}],
    [{"LOWER": "more"}, {"LOWER": "records"}],
    [{"LOWER": "most"}, {"LOWER": "entries"}],
    [{"LOWER": "busiest"}, {"LOWER": "date"}],
    [{"LOWER": "date"}, {"LOWER": "has"}, {"LOWER": "more"}],
    [{"LOWER": "date"}, {"LOWER": "has"}, {"LOWER": "most"}],
])

# ── Intent priority ────────────────────────────────────────────────────────
INTENT_PRIORITY = {
    "DATE_GROUP": 10,
    "AVERAGE":    9,
    "MAXIMUM":    9,
    "MINIMUM":    9,
    "COUNT":      8,
    "ANOMALY":    8,
    "LATEST":     7,
    "LIST":       6,
}


@dataclass
class NLPResult:
    corrected_text: str   = ""
    intent:         str   = "unknown"
    engine_side:    str   = "both"
    metric:         str   = ""
    date_filter:    str   = ""
    column_hint:    str   = ""
    sql:            str   = ""
    confidence:     float = 0.0
    entities:       dict  = field(default_factory=dict)


# ── Helpers ────────────────────────────────────────────────────────────────
def _spell_correct(text: str) -> str:
    return " ".join(TYPO_MAP.get(tok.lower().strip("?.,!"), tok) for tok in text.split())

def _dual_date_sql(day: int, month: int, year: int) -> str:
    return (
        f"(CAST(DateAndTime AS VARCHAR) LIKE '%{day:02d}-{month:02d}-{year}%' "
        f"OR CAST(DateAndTime AS VARCHAR) LIKE '%{month}/{day}/{year}%' "
        f"OR CAST(DateAndTime AS VARCHAR) LIKE '%{year}-{month:02d}-{day:02d}%' "
        f"OR CAST(DateAndTime AS VARCHAR) LIKE '%{day}/{month}/{year}%')"
    )

def _parse_date(text: str) -> str:
    t = text.lower()
    m = re.search(
        r'(\d{1,2})\s+(' + '|'.join(MONTHS) + r')\s+(\d{4})|'
        r'(' + '|'.join(MONTHS) + r')\s+(\d{1,2})[,\s]+(\d{4})', t
    )
    if m:
        g = m.groups()
        if g[0]:
            d, mon, y = int(g[0]), MONTHS[g[1]], int(g[2])
        else:
            d, mon, y = int(g[4]), MONTHS[g[3]], int(g[5])
        return _dual_date_sql(d, mon, y)
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', t)
    if m:
        return _dual_date_sql(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    m = re.search(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', t)
    if m:
        return _dual_date_sql(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return ""

def _detect_intent_spacy(text: str) -> tuple:
    doc     = nlp(text.lower())
    matches = matcher(doc)
    if not matches:
        return "unknown", 0.0
    intent_hits = {}
    for match_id, start, end in matches:
        label = nlp.vocab.strings[match_id]
        intent_hits[label] = intent_hits.get(label, 0) + 1
    best_intent = max(
        intent_hits,
        key=lambda x: (INTENT_PRIORITY.get(x, 0), intent_hits[x])
    )
    total_hits = intent_hits[best_intent]
    confidence = min(total_hits * 0.35 + 0.40, 1.0)
    return best_intent.lower(), round(confidence, 3)

def _extract_entities(text: str, cols: list) -> dict:
    low, ents = text.lower(), {}
    words = set(low.split())
    ents["engine_side"] = (
        "port" if words & PORT_WORDS and not words & STBD_WORDS else
        "stbd" if words & STBD_WORDS and not words & PORT_WORDS else
        "both"
    )
    # Exact column name match
    for col in cols:
        if col.lower() in low:
            ents["exact_col"]   = col
            ents["column_hint"] = col
            if col.startswith("EP_"):
                ents["engine_side"] = "port"
            elif col.startswith("STBD_"):
                ents["engine_side"] = "stbd"
            break
    # Metric keyword match
    if not ents.get("column_hint"):
        for kw, frag in METRIC_MAP.items():
            if kw in low:
                ents["metric"]      = kw
                ents["column_hint"] = frag
                break
    # Threshold
    m = re.search(r'(above|over|greater than|below|under|less than|equal to)\s*(\d+\.?\d*)', low)
    if m:
        op_map = {"above":">","over":">","greater than":">",
                  "below":"<","under":"<","less than":"<","equal to":"="}
        ents["threshold"] = {"op": op_map[m.group(1)], "value": m.group(2)}
    # Date
    date_sql = _parse_date(low)
    if date_sql:
        ents["date_sql"] = date_sql
    # Limit
    m = re.search(r'\b(top|first|last)\s+(\d+)\b', low)
    if m:
        ents["limit"] = int(m.group(2))
    else:
        pat = r'\b(top|first|last)\s+(' + '|'.join(WORD_NUMBERS.keys()) + r')\b'
        m = re.search(pat, low)
        if m:
            ents["limit"] = WORD_NUMBERS[m.group(2)]
        else:
            pat2 = r'\b(' + '|'.join(WORD_NUMBERS.keys()) + r')\s+(entry|entries|records|rows|data)\b'
            m2 = re.search(pat2, low)
            if m2:
                ents["limit"] = WORD_NUMBERS[m2.group(1)]
    return ents

def _pick_col(ents: dict, side: str, cols: list) -> str:
    hint   = ents.get("column_hint", "").lower()
    prefix = {"port": "EP_", "stbd": "STBD_", "both": "EP_"}[side]
    exact  = ents.get("exact_col", "")
    if exact and exact in cols:
        return exact
    hits = [c for c in cols if hint in c.lower() and c.startswith(prefix)]
    if hits:
        return hits[0]
    hits = [c for c in cols if hint in c.lower()]
    if hits:
        return hits[0]
    return next((c for c in cols if c.startswith(prefix)), cols[0])

def _where(ents: dict) -> str:
    parts = []
    if ents.get("date_sql"):
        parts.append(ents["date_sql"])
    if ents.get("threshold") and ents.get("_col"):
        t = ents["threshold"]
        parts.append(f"CAST({ents['_col']} AS DOUBLE) {t['op']} {t['value']}")
    return ("WHERE " + " AND ".join(parts)) if parts else ""

def _agg_sql(func: str, ents: dict, cols: list, table: str) -> tuple:
    sides = ["port", "stbd"] if ents.get("engine_side", "both") == "both" else [ents["engine_side"]]
    sel   = []
    for s in sides:
        col = _pick_col(ents, s, cols)
        ents["_col"] = col
        sel.append(f"ROUND({func}(CAST({col} AS DOUBLE)), 2) AS {func.lower()}_{col}")
    return f"SELECT {', '.join(sel)} FROM {table} {_where(ents)}".strip(), \
           0.90 if ents.get("column_hint") else 0.75

def _build_sql(intent: str, ents: dict, cols: list, table: str) -> tuple:
    lim, w = ents.get("limit", 20), _where(ents)
    if intent == "average":    return _agg_sql("AVG", ents, cols, table)
    if intent == "maximum":    return _agg_sql("MAX", ents, cols, table)
    if intent == "minimum":    return _agg_sql("MIN", ents, cols, table)
    if intent == "count":
        return f"SELECT COUNT(*) AS total FROM {table} {w}".strip(), 0.92
    if intent == "latest":
        return f"SELECT * FROM {table} {w} ORDER BY DateAndTime DESC LIMIT {lim}".strip(), 0.90
    if intent == "list":
        return f"SELECT * FROM {table} {w} LIMIT {lim}".strip(), 0.80
    if intent == "date_group":
        return (
            f"SELECT CAST(DateAndTime AS VARCHAR) AS date, COUNT(*) AS record_count "
            f"FROM {table} "
            f"GROUP BY CAST(DateAndTime AS VARCHAR) "
            f"ORDER BY record_count DESC LIMIT 10"
        ), 0.92
    if intent == "anomaly":
        col = _pick_col(ents, "port" if ents.get("engine_side","both") == "both"
                        else ents["engine_side"], cols)
        return (
            f"SELECT DateAndTime, {col}, "
            f"ROUND(AVG(CAST({col} AS DOUBLE)) OVER(), 2) AS avg_val "
            f"FROM {table} WHERE "
            f"ABS(CAST({col} AS DOUBLE) - AVG(CAST({col} AS DOUBLE)) OVER()) "
            f"> 2 * STDDEV(CAST({col} AS DOUBLE)) OVER() LIMIT 20"
        ), 0.80
    return "", 0.0


# ── Entry point ────────────────────────────────────────────────────────────
def run_nlp_pipeline(question: str, safe_columns: list, table: str = "engine_data") -> NLPResult:
    res                  = NLPResult()
    res.corrected_text   = _spell_correct(question)
    res.intent, int_conf = _detect_intent_spacy(res.corrected_text)
    ents                 = _extract_entities(res.corrected_text, safe_columns)
    res.entities         = ents
    res.engine_side      = ents.get("engine_side", "both")
    res.metric           = ents.get("metric", "")
    res.date_filter      = ents.get("date_sql", "")
    res.column_hint      = ents.get("column_hint", "")

    if res.intent != "unknown":
        try:
            res.sql, tmpl_conf = _build_sql(res.intent, ents, safe_columns, table)
            res.confidence     = round(int_conf * 0.4 + tmpl_conf * 0.6, 3)
        except Exception:
            res.confidence = 0.0

    # Date boost
    if ents.get("date_sql") and res.confidence < 0.70:
        res.intent     = "list" if res.intent == "unknown" else res.intent
        res.sql, _     = _build_sql(res.intent, ents, safe_columns, table)
        res.confidence = 0.75
        print(f"[NLP] Date boost → intent={res.intent} confidence={res.confidence}")

    return res