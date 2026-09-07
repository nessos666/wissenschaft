"""
Response Cache — SQLite-basierter Cache für wissenschaftliche Queries.
TTL: 24h für Metadaten, 7d für Volltext.
"""
import sqlite3, json, hashlib, time
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass

DB_PATH = Path.home() / ".hermes" / "wissenschaft_cache.db"

@dataclass
class CacheEntry:
    key: str
    query: str
    results_json: str
    result_count: int
    sources_used: str
    created_at: str
    expires_at: str

class ResponseCache:
    def __init__(self, db_path: str = None):
        self.db = db_path or str(DB_PATH)
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    results_json TEXT NOT NULL,
                    result_count INTEGER DEFAULT 0,
                    sources_used TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires_at)")
            conn.commit()
    
    def _make_key(self, query: str, depth: str = "standard") -> str:
        return hashlib.sha256(f"{query.lower().strip()}|{depth}".encode()).hexdigest()[:16]
    
    def get(self, query: str, depth: str = "standard") -> dict | None:
        """Holt gecachte Ergebnisse. None wenn nicht vorhanden oder abgelaufen."""
        key = self._make_key(query, depth)
        with sqlite3.connect(self.db) as conn:
            row = conn.execute(
                "SELECT results_json, expires_at FROM cache WHERE key = ?", (key,)
            ).fetchone()
        
        if not row:
            return None
        
        results_json, expires_at = row
        if datetime.fromisoformat(expires_at) < datetime.now():
            self._delete(key)
            return None
        
        return json.loads(results_json)
    
    def set(self, query: str, results: list[dict], depth: str = "standard",
            sources: list[str] = None, ttl_hours: int = 24):
        """Speichert Ergebnisse im Cache."""
        key = self._make_key(query, depth)
        now = datetime.now()
        expires = now + timedelta(hours=ttl_hours)
        
        with sqlite3.connect(self.db) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cache (key, query, results_json, result_count, sources_used, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                key, query, json.dumps(results, ensure_ascii=False),
                len(results), ",".join(sources or []),
                now.isoformat(), expires.isoformat(),
            ))
            conn.commit()
    
    def _delete(self, key: str):
        with sqlite3.connect(self.db) as conn:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()
    
    def clear_expired(self) -> int:
        """Löscht abgelaufene Einträge."""
        with sqlite3.connect(self.db) as conn:
            cursor = conn.execute("DELETE FROM cache WHERE expires_at < ?", (datetime.now().isoformat(),))
            conn.commit()
            return cursor.rowcount
    
    def stats(self) -> dict:
        """Cache-Statistik."""
        with sqlite3.connect(self.db) as conn:
            total = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
            active = conn.execute("SELECT COUNT(*) FROM cache WHERE expires_at > ?", (datetime.now().isoformat(),)).fetchone()[0]
            expired = total - active
        return {"total": total, "active": active, "expired": expired, "db_path": self.db}

if __name__ == "__main__":
    cache = ResponseCache()
    
    # Test: speichern + lesen
    test_results = [{"title": "Test Paper", "source": "OpenAlex"}]
    cache.set("machine learning", test_results, ttl_hours=24)
    
    cached = cache.get("machine learning")
    print(f"Cache hit: {cached is not None}")
    print(f"Results: {len(cached) if cached else 0}")
    
    no_cache = cache.get("xyzzy something never searched")
    print(f"Cache miss: {no_cache is None}")
    
    cleaned = cache.clear_expired()
    stats = cache.stats()
    print(f"Stats: {stats}")
