"""PDF-Downloader (Verbesserung 3) — lädt OA-PDFs der Treffer ins Dossier.

Strategie je Treffer:
1. pdf_url vorhanden → direkt laden
2. sonst DOI vorhanden → Unpaywall (vendored, MCP-frei) sucht beste OA-URL
3. sonst → überspringen (kein PDF verfügbar, kein Fehler)

Sicher: bereinigte Dateinamen, Timeout, nie crashen. Liefert Liste der
geladenen Pfade + Statistik.
"""
import re
import sys
from pathlib import Path

import requests

VENDOR = Path(__file__).resolve().parents[1] / "vendor" / "paper_search_mcp"
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from paper_search_mcp.academic_platforms.unpaywall import UnpaywallResolver  # noqa: E402

HEADERS = {"User-Agent": "WissenschaftTool/4.0 (+https://github.com/nessos666; mailto:kontakt@wissenshaft.tool)"}
TIMEOUT = 40


def _sicherer_name(titel: str, doi: str, i: int) -> str:
    """Bereinigter Dateiname: <nr>_<slug>[_<doi-slug>].pdf"""
    slug = re.sub(r"[^A-Za-z0-9]+", "_", titel or "paper").strip("_")[:60]
    doi_slug = re.sub(r"[^A-Za-z0-9]+", "", doi or "")[-20:]
    basis = f"{i:02d}_{slug}" + (f"_{doi_slug}" if doi_slug else "")
    return basis[:90] + ".pdf"


def _lade(url: str, ziel: Path) -> bool:
    """Eine URL als PDF laden. True bei Erfolg."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT,
                         allow_redirects=True, stream=True)
        if r.status_code != 200:
            return False
        ct = r.headers.get("Content-Type", "")
        # Nur PDFs akzeptieren (kein HTML-Fehler-Trap)
        if "pdf" not in ct.lower() and not url.lower().endswith(".pdf"):
            # Trotzdem versuchen wenn Inhalt nach PDF aussieht
            head = r.raw.read(5) if hasattr(r, "raw") else b""
            if not head.startswith(b"%PDF"):
                return False
        with open(ziel, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        # Verifizieren: echte PDF-Datei?
        if ziel.stat().st_size > 1000:
            with open(ziel, "rb") as f:
                if f.read(4) == b"%PDF":
                    return True
        ziel.unlink(missing_ok=True)
        return False
    except Exception:
        return False


def lade_pdfs(treffer: list, ziel_dir: Path, unpaywall_email: str = "") -> dict:
    """Lädt OA-PDFs der Treffer nach ziel_dir/pdfs/. Nie crashen.

    Liefert {"geladen": [pfad...], "fehlgeschlagen": int, "ohne_pdf": int,
    "gesamt": len(treffer)}.
    """
    pdf_dir = Path(ziel_dir) / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    resolver = None
    if unpaywall_email:
        try:
            resolver = UnpaywallResolver(email=unpaywall_email)
        except Exception:
            resolver = None

    geladen = []
    fehlgeschlagen = 0
    ohne_pdf = 0

    for i, t in enumerate(treffer, 1):
        if not isinstance(t, dict):
            continue
        titel = t.get("title") or f"paper_{i}"
        doi = (t.get("doi") or "").strip()
        url = (t.get("pdf_url") or "").strip()
        ziel = pdf_dir / _sicherer_name(titel, doi, i)

        # 1) pdf_url direkt
        if url and _lade(url, ziel):
            geladen.append(str(ziel))
            continue

        # 2) Unpaywall-OA-Fallback über DOI
        if doi and resolver is not None:
            try:
                oa_url = resolver.resolve_best_pdf_url(doi)
                if oa_url and _lade(oa_url, ziel):
                    geladen.append(str(ziel))
                    continue
            except Exception:
                pass

        # 3) Kein PDF verfügbar
        if not url and not doi:
            ohne_pdf += 1
        else:
            fehlgeschlagen += 1

    return {"geladen": geladen, "fehlgeschlagen": fehlgeschlagen,
            "ohne_pdf": ohne_pdf, "gesamt": len(treffer)}


if __name__ == "__main__":
    import sys as _s
    if len(_s.argv) < 3:
        print("Nutzung: lade_pdfs.py <json-datei> <ziel-ordner>")
        _s.exit(1)
    import json
    with open(_s.argv[1]) as f:
        treffer = json.load(f)
    stat = lade_pdfs(treffer, Path(_s.argv[2]),
                     unpaywall_email="kontakt@wissenshaft.tool")
    print(f"Geladen: {len(stat['geladen'])} | Fehlgeschlagen: "
          f"{stat['fehlgeschlagen']} | Ohne PDF: {stat['ohne_pdf']} "
          f"| Gesamt: {stat['gesamt']}")
    for p in stat["geladen"]:
        print(f"  ✓ {p}")
