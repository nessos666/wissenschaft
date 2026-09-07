"""
Query Analyzer V2 — mit Boolean-Suche (AND/OR/NOT), Domain-Erkennung, Synonymen.
"""
import re, json
from dataclasses import dataclass, field, asdict

DOMAIN_KEYWORDS = {
    "trading": ["trading", "futures", "market", "nq", "es", "orderflow", "microstructure", "fvg", "ict", "smc", "fair value gap", "backtest", "strategy"],
    "finance": ["finance", "economics", "yield", "bond", "equity", "portfolio", "risk", "hedge", "option", "derivative"],
    "medicine": ["medizin", "klinisch", "patient", "therapie", "diagnose", "studie", "pharma", "impfstoff", "erkrankung", "symptom", "infection", "maternal", "autism", "genetics"],
    "computer_science": ["python", "code", "algorithm", "machine learning", "deep learning", "neural", "wasm", "browser", "compiler", "pyscript", "api", "transformer", "attention", "llm", "bert", "gpt", "embedding", "tokenization"],
    "biology": ["soil", "microbiome", "permaculture", "bacteria", "fungi", "plant", "ecosystem", "biodiversity"],
    "physics": ["physik", "quantum", "particle", "higgs", "lhc", "cern", "black hole", "black holes", "relativity", "cosmology", "astrophysics", "gravity", "string theory"],
    "mathematics": ["mathematik", "theorem", "proof", "algebra", "geometry", "number", "topology", "stochastic", "probability", "differential equation", "calculus", "manifold"],
    "psychology": ["productivity", "remote work", "meta analysis", "psychology", "behavior", "cognitive"],
}

SYNONYM_MAP = {
    "fvg": ["fair value gap", "imbalance", "price gap"],
    "ict": ["inner circle trader", "smart money concepts", "smc"],
    "nq": ["nasdaq-100 futures", "e-mini nasdaq"],
    "es": ["s&p 500 futures", "e-mini s&p"],
    "microbiome": ["microbial community", "soil bacteria", "rhizosphere"],
    "pyscript": ["python in browser", "webassembly python", "pyodide"],
    "remote work": ["work from home", "telework", "distributed work"],
    "meta analysis": ["systematic review", "meta-analysis", "evidence synthesis"],
}

@dataclass
class StructuredQuery:
    original: str
    keywords_de: list[str] = field(default_factory=list)
    keywords_en: list[str] = field(default_factory=list)
    synonyms_en: list[str] = field(default_factory=list)
    domain_guess: str = "multidisciplinary"
    domain_confidence: float = 0.0
    search_terms_en: list[str] = field(default_factory=list)
    boolean_structure: str = "and"  # and/or
    excluded_terms: list[str] = field(default_factory=list)


def parse_boolean(query: str) -> tuple[str, list[str]]:
    """Parst Boolean-Operatoren AND/OR/NOT aus Query."""
    excluded = []
    clean = query
    
    # NOT / -term
    not_pattern = re.findall(r'(?:NOT\s+|-\s*)(\w+(?:\s+\w+)*?)(?=\s+(?:AND|OR|NOT|$)|\s*$)', query, re.IGNORECASE)
    excluded = [t.strip().lower() for t in not_pattern]
    
    # Entferne NOT-Terme für die eigentliche Suche
    clean = re.sub(r'\bNOT\s+\w+(?:\s+\w+)*?(?=\s+(?:AND|OR|$)|\s*$)', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'-\s*\w+', '', clean)
    
    # Erkenne Struktur
    has_or = bool(re.search(r'\bOR\b', clean, re.IGNORECASE))
    
    # Extrahiere AND/OR-Gruppen
    if has_or:
        boolean_structure = "or"
        groups = re.split(r'\s+OR\s+', clean, flags=re.IGNORECASE)
    else:
        boolean_structure = "and"
        groups = re.split(r'\s+AND\s+', clean, flags=re.IGNORECASE)
    
    groups = [g.strip() for g in groups if g.strip()]
    clean_query = " ".join(groups) if groups else clean.strip()
    
    return clean_query, excluded, boolean_structure


def analyze_query(query: str) -> StructuredQuery:
    """Analysiert Nutzerfrage mit Boolean-Support."""
    # Boolean parsen
    clean_query, excluded, bool_struct = parse_boolean(query)
    query_lower = clean_query.lower().strip()
    
    # Domain-Vermutung
    domain_scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw.lower()) + r'\b', query_lower))
        if score > 0:
            domain_scores[domain] = score
    
    best_domain = max(domain_scores, key=domain_scores.get) if domain_scores and max(domain_scores.values()) > 0 else "multidisciplinary"
    best_confidence = min(max(domain_scores.values()) / 5.0, 1.0) if domain_scores else 0.2
    
    # Keywords
    words = re.findall(r'[a-zA-ZäöüßÄÖÜ]{3,}', query_lower)
    stopwords = {'the','and','for','mit','und','von','der','die','das','ist','ein','eine','was','wie','bei','auf','aus','not','or'}
    keywords = [w for w in words if w.lower() not in stopwords]
    
    # Synonyme
    synonyms = []
    for kw in keywords:
        if kw in SYNONYM_MAP:
            synonyms.extend(SYNONYM_MAP[kw])
    for kw in excluded:
        if kw in SYNONYM_MAP:
            synonyms.extend(SYNONYM_MAP[kw])
    
    # Suchterme
    search_terms = [clean_query]
    if bool_struct == "or":
        groups = re.split(r'\s+OR\s+', clean_query, flags=re.IGNORECASE)
        search_terms = [g.strip() for g in groups if g.strip()]
    search_terms.extend(synonyms)
    
    return StructuredQuery(
        original=query,
        keywords_de=keywords,
        keywords_en=[clean_query],
        synonyms_en=synonyms,
        domain_guess=best_domain,
        domain_confidence=best_confidence,
        search_terms_en=search_terms[:5],
        boolean_structure=bool_struct,
        excluded_terms=excluded,
    )


if __name__ == "__main__":
    import sys
    q = analyze_query(sys.argv[1] if len(sys.argv) > 1 else "FVG AND microstructure NOT bitcoin")
    print(json.dumps(asdict(q), indent=2, ensure_ascii=False))
