#!/usr/bin/env python3
"""
qdrant_save.py V1.1 — Rebuilt 22.07.2026
Speichert wissenschaftliche Ergebnisse in Qdrant Collection 'wissenschaft_results'.

USAGE:
  qdrant_save.py --input /tmp/wissenschaft_results.json --query "QUERY"
  qdrant_save.py --list-collections

Vector: 384-dim hash-based fallback (kein sentence-transformers noetig)
"""

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

QDRANT_URL = "http://localhost:6335"
COLLECTION = "wissenschaft_results"
VECTOR_DIM = 384


def hash_embed(text, dim=VECTOR_DIM):
    """Hash-basierter Embedding-Vektor."""
    h = hashlib.sha256(text.encode()).digest()
    stretched = (h * (dim // 32 + 1))[:dim]
    return [float(b) / 255.0 for b in stretched]


def ensure_collection(collection_name):
    """Create collection if not exists."""
    url = f"{QDRANT_URL}/collections/{collection_name}"
    try:
        req = urllib.request.Request(url)
        resp = json.loads(urllib.request.urlopen(req).read())
        if resp.get("result", {}).get("status") == "green":
            return True
    except Exception:
        pass

    data = json.dumps({"vectors": {"size": VECTOR_DIM, "distance": "Cosine"}}).encode()
    req = urllib.request.Request(url, data=data, method="PUT",
                                 headers={"Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req).read())
    return resp.get("result")


def scroll_max_id(collection_name):
    """Get max integer ID from collection."""
    url = f"{QDRANT_URL}/collections/{collection_name}/points/scroll"
    data = json.dumps({"limit": 1000, "with_payload": False}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req).read())
    pts = resp.get("result", {}).get("points", [])
    int_ids = [p["id"] for p in pts if isinstance(p["id"], int)]
    return max(int_ids) if int_ids else 0


def insert_paper(paper, point_id, collection_name):
    """Insert a single paper as a Qdrant point."""
    text = f"{paper.get('title','')} {paper.get('abstract','')} {paper.get('authors','')}"
    vector = hash_embed(text)
    payload = {
        "title": paper.get("title", ""),
        "doi": paper.get("doi", ""),
        "url": paper.get("url", ""),
        "abstract": paper.get("abstract", "")[:1000],
        "authors": paper.get("authors", ""),
        "year": paper.get("year", ""),
        "source": paper.get("source", "unknown"),
        "text": text[:2000],
    }
    
    point = {"id": point_id, "vector": vector, "payload": payload}
    url = f"{QDRANT_URL}/collections/{collection_name}/points?wait=true"
    data = json.dumps({"points": [point]}).encode()
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"}, method="PUT")
    resp = json.loads(urllib.request.urlopen(req).read())
    return resp.get("result", {}).get("status") == "completed"


def list_collections():
    """List all Qdrant collections."""
    url = f"{QDRANT_URL}/collections"
    req = urllib.request.Request(url)
    resp = json.loads(urllib.request.urlopen(req).read())
    for c in resp.get("result", {}).get("collections", []):
        name = c.get("name", "?")
        points = c.get("points_count", "?")
        print(f"  {name}: {points} points")


def main():
    parser = argparse.ArgumentParser(description="Qdrant Save for /wissenschaft")
    parser.add_argument("--input", help="JSON input file with papers")
    parser.add_argument("--query", default="", help="Search query (for provenance)")
    parser.add_argument("--collection", default=COLLECTION, help=f"Collection name (default: {COLLECTION})")
    parser.add_argument("--list-collections", action="store_true", help="List all collections")

    args = parser.parse_args()

    if args.list_collections:
        list_collections()
        return

    if not args.input:
        print("ERROR: --input required")
        sys.exit(1)

    collection_name = args.collection

    # Load papers
    input_data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    papers = input_data.get("papers", [])
    if not papers and isinstance(input_data, list):
        papers = input_data

    if not papers:
        print("ERROR: Keine Paper in Input-Datei gefunden. Format: {\"papers\": [...]}")
        sys.exit(1)

    # Ensure collection
    ensure_collection(collection_name)
    print(f"Collection '{collection_name}' bereit.")

    # Get max ID
    max_id = scroll_max_id(collection_name)
    print(f"Max ID: {max_id}, inserting {len(papers)} papers...")

    # Insert
    inserted = 0
    for paper in papers:
        max_id += 1
        try:
            ok = insert_paper(paper, max_id, collection_name)
            if ok:
                inserted += 1
                print(f"  [{max_id}] {paper.get('title','?')[:70]}")
            else:
                print(f"  [FAIL {max_id}] {paper.get('title','?')[:50]}")
        except Exception as e:
            print(f"  [ERROR {max_id}] {e}")
            max_id -= 1

    print(f"\n{inserted}/{len(papers)} papers gespeichert in '{collection_name}' (IDs {max_id - len(papers) + 1}-{max_id})")


if __name__ == "__main__":
    main()
