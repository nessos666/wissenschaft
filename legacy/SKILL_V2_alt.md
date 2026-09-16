---
name: wissenschaft
description: "Wissenschaftliches Recherche-Tool V2 — 4-Agent-Pipeline + Verifier + Skills + Qdrant"
version: 2.0.0
---

# /wissenschaft V2

## Ablauf

### Phase 1: Interaktion
User: `/wissenschaft`
→ Frage: "Thema?"
→ Frage: "Tiefe? [1] schnell [2] standard [3] tief"

### Phase 2: Suchplan + MCP-Calls
```bash
python3 ~/HAUPTLAGER/03_PROJEKTE/XX_WissenschaftSkill/wissenschaft_cli.py "QUERY" --tiefe TIEFE --plan
```
→ MCP-Calls parallel ausführen (5× schneller als sequentiell)
→ Ergebnisse als JSON speichern: `/tmp/wissenschaft_results.json`

### Phase 3: 4-Agent-Pipeline
```bash
python3 ~/HAUPTLAGER/03_PROJEKTE/XX_WissenschaftSkill/wissenschaft_cli.py "QUERY" --orchestrate --input /tmp/wissenschaft_results.json
```
→ Researcher → Verifier → Synthesis → Reviewer

### Phase 4: Qdrant
```bash
python3 ~/HAUPTLAGER/03_PROJEKTE/XX_WissenschaftSkill/qdrant_save.py \
  --collection wissenschaft_results \
  --input /tmp/wissenschaft_results.json \
  --query "QUERY"
```

### Phase 5: Ergebnis
Executive Summary + Trust-Scores + Top-10 + Exporte (.md .bib .ris .json)

## Was V2 neu kann

- **4-Agent-Team** statt Pipeline
- **Trust-Score** pro Paper (DOI/URL/Authors-Check)
- **Skill-System** — neue Quellen via SKILL.md
- **Qdrant** — Ergebnisse wiederfindbar
- **5× schneller** durch Parallel-Suche

## NICHT
- NICHT selbst suchen ohne Tool
- NICHT MCP-Calls erfinden
- Semantic Scholar 0 Treffer → `"degraded": true`
