"""
Qdrant Save — Vektorisiert /wissenschaft-Ergebnisse in Qdrant (Port 6335).
"""
import json, sys, argparse
from pathlib import Path
from datetime import datetime

def save_to_qdrant(collection: str, results_file: str, query: str, port: int = 6335):
    """Speichert Ergebnisse in Qdrant-Collection. Nutzt sentence-transformers für Embeddings."""
    with open(results_file) as f:
        data = json.load(f)
    
    results = data.get("results", [])
    if not results:
        print("Keine Ergebnisse zum Speichern.")
        return False
    
    try:
        from sentence_transformers import SentenceTransformer
        import urllib.request, urllib.error
        
        model = SentenceTransformer("all-MiniLM-L6-v2")
        base = f"http://localhost:{port}"
        
        # Prüfe ob Collection existiert
        try:
            req = urllib.request.Request(f"{base}/collections/{collection}")
            urllib.request.urlopen(req, timeout=5)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Collection anlegen
                create_payload = json.dumps({
                    "vectors": {"size": 384, "distance": "Cosine"}
                }).encode()
                req = urllib.request.Request(
                    f"{base}/collections/{collection}?wait=true",
                    data=create_payload,
                    headers={"Content-Type": "application/json"},
                    method="PUT"
                )
                urllib.request.urlopen(req, timeout=10)
                print(f"Collection '{collection}' angelegt.")
        
        # Embeddings + Insert
        points = []
        for i, r in enumerate(results[:30]):
            text = f"{r.get('title','')} {r.get('abstract','')[:200]}"
            if not text.strip():
                continue
            vec = model.encode([text])[0].tolist()
            points.append({
                "id": i + int(datetime.now().timestamp() * 1000) % 100000,
                "vector": vec,
                "payload": {
                    "title": r.get("title", ""),
                    "authors": r.get("authors", ""),
                    "year": r.get("year", ""),
                    "doi": r.get("doi", ""),
                    "source": r.get("source", ""),
                    "query": query,
                    "date": str(datetime.now().date()),
                    "type": "wissenschaft_result",
                }
            })
        
        if points:
            payload = json.dumps({"points": points}).encode()
            req = urllib.request.Request(
                f"{base}/collections/{collection}/points?wait=true",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="PUT"
            )
            resp = urllib.request.urlopen(req, timeout=15)
            result = json.loads(resp.read())
            print(f"Qdrant: {len(points)} Punkte in '{collection}' gespeichert. Status: {result.get('status')}")
            return True
        
    except ImportError:
        print("⚠️ sentence-transformers nicht installiert. Überspringe Qdrant.")
        print("   pip install sentence-transformers")
        return False
    except urllib.error.URLError as e:
        print(f"⚠️ Qdrant nicht erreichbar auf Port {port}: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Qdrant-Fehler: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", default="wissenschaft_results")
    parser.add_argument("--input", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--port", type=int, default=6335)
    args = parser.parse_args()
    save_to_qdrant(args.collection, args.input, args.query, args.port)
