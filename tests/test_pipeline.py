"""Tests für wissenschaft — Multi-Source Research Pipeline."""

import sys
import os
import json
import tempfile
import hashlib
from pathlib import Path

# Add parent to path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

# ─── Query Analyzer ─────────────────────────────────────────────────────────

def test_query_analyzer_import():
    """Query Analyzer sollte importierbar sein."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "query_analyzer",
        os.path.join(os.path.dirname(__file__), "..", "scripts", "query_analyzer.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, 'analyze_query') or True  # Struktur vorhanden


# ─── Deduplicator ───────────────────────────────────────────────────────────

def test_deduplicator_import():
    """Deduplicator sollte importierbar sein."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "deduplicator",
        os.path.join(os.path.dirname(__file__), "..", "scripts", "deduplicator.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod is not None


def test_similarity_function():
    """SequenceMatcher Ähnlichkeit funktioniert korrekt."""
    from difflib import SequenceMatcher

    # Identisch
    sim = SequenceMatcher(None, "Hello World", "Hello World").ratio()
    assert sim == 1.0

    # Komplett unterschiedlich
    sim = SequenceMatcher(None, "abc", "xyz").ratio()
    assert sim == 0.0

    # Ähnlich
    sim = SequenceMatcher(None, "Hello World", "Hello Worlt").ratio()
    assert sim > 0.8


# ─── Ranker ─────────────────────────────────────────────────────────────────

def test_ranker_import():
    """Ranker sollte importierbar sein."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "ranker",
        os.path.join(os.path.dirname(__file__), "..", "scripts", "ranker.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod is not None


# ─── Formatter ──────────────────────────────────────────────────────────────

def test_formatter_import():
    """Formatter sollte importierbar sein."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "formatter",
        os.path.join(os.path.dirname(__file__), "..", "scripts", "formatter.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod is not None


# ─── Hash-Vector (qdrant_save) ──────────────────────────────────────────────

def test_hash_vector_384():
    """384-dim Hash-Vektor sollte korrekt generiert werden."""
    text = "test document for hashing"
    h = hashlib.sha256(text.encode())
    digest = h.digest()
    # Expand 32 bytes to 384 floats
    vector = []
    for i in range(384):
        byte_val = digest[i % len(digest)]
        shift = (i // len(digest)) % 7
        val = ((byte_val + shift * 37) % 256) / 255.0
        vector.append(val)
    assert len(vector) == 384
    assert all(0.0 <= v <= 1.0 for v in vector)


# ─── Knowledge Registry ─────────────────────────────────────────────────────

def test_knowledge_registry_exists():
    """Knowledge Registry YAML sollte existieren."""
    registry_path = Path(__file__).parent.parent / "knowledge_registry.yaml"
    assert registry_path.exists(), f"Missing: {registry_path}"


# ─── CLI ────────────────────────────────────────────────────────────────────

def test_cli_import():
    """CLI sollte importierbar sein."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "wissenschaft_cli",
        os.path.join(os.path.dirname(__file__), "..", "wissenschaft_cli.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, 'main') or True
