"""
Async Dispatcher — Parallele Suche über mehrere Quellen.
Nutzt ThreadPool für I/O-gebundene MCP-Calls.
"""
import time, json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

@dataclass
class AsyncResult:
    source_name: str
    success: bool
    results: list[dict] = field(default_factory=list)
    error: str = ""
    duration_ms: float = 0.0
    result_count: int = 0

def search_single_sync(source_name: str, query: str) -> list[dict]:
    """Synchrone Einzelsuche (Platzhalter — wird vom LLM via MCP ersetzt).
    In Produktion: LLM führt die MCP-Calls aus und übergibt Ergebnisse."""
    # Diese Funktion ist ein Platzhalter.
    # Die eigentliche Suche passiert via MCP-Tools durch den LLM.
    # Hier nur die Infrastruktur für parallele Ausführung.
    return []

def dispatch_parallel(sources: list[dict], query: str, max_workers: int = 5) -> list[AsyncResult]:
    """Führt Suchen parallel aus (ThreadPool)."""
    results = []
    t0 = time.time()
    
    with ThreadPoolExecutor(max_workers=min(max_workers, len(sources))) as executor:
        futures = {}
        for src in sources:
            name = src.get("name", src.get("tool", "unknown"))
            future = executor.submit(search_single_sync, name, query)
            futures[future] = name
        
        for future in as_completed(futures):
            name = futures[future]
            t1 = time.time()
            try:
                data = future.result(timeout=30)
                results.append(AsyncResult(
                    source_name=name,
                    success=True,
                    results=data,
                    duration_ms=(time.time()-t1)*1000,
                    result_count=len(data),
                ))
            except Exception as e:
                results.append(AsyncResult(
                    source_name=name,
                    success=False,
                    error=str(e)[:200],
                    duration_ms=(time.time()-t1)*1000,
                ))
    
    return results

def benchmark_sequential_vs_parallel(sources: list[str], query: str) -> dict:
    """Vergleicht sequentielle vs. parallele Laufzeit (Simulation)."""
    # Simulation: Jede Quelle braucht ~8s
    SIMULATED_DELAY = 1.0  # 1s pro Quelle für Benchmark
    
    # Sequentiell
    t0 = time.time()
    for _ in sources:
        time.sleep(SIMULATED_DELAY)
    seq_time = time.time() - t0
    
    # Parallel (theoretisch)
    par_time = SIMULATED_DELAY  # Alle gleichzeitig
    
    return {
        "sources": len(sources),
        "sequential_seconds": round(seq_time, 1),
        "parallel_seconds": round(par_time, 1),
        "speedup": round(seq_time / max(par_time, 0.001), 1),
        "note": "Simulation: 1s pro Quelle. In Produktion ~8s pro MCP-Call.",
    }

if __name__ == "__main__":
    # Benchmark
    sources = ["OpenAlex", "CrossRef", "Semantic Scholar", "arXiv", "SSRN"]
    bm = benchmark_sequential_vs_parallel(sources, "test")
    print(f"Sequentiell: {bm['sequential_seconds']}s")
    print(f"Parallel:   {bm['parallel_seconds']}s")
    print(f"Speedup:    {bm['speedup']}×")
    print(f"Bei echten 8s/Call: {bm['speedup']*8:.0f}s vs {8:.0f}s = {bm['speedup']}× schneller")
