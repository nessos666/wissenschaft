"""
Skill Loader — Lädt SKILL.md-Dateien aus ~/.wissenschaft/skills/
Jede SKILL.md definiert Quellen für eine Domain.
"""
import yaml, re
from pathlib import Path
from dataclasses import dataclass, field

@dataclass
class Skill:
    name: str
    domain: str
    triggers: list[str] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    path: str = ""

class SkillLoader:
    def __init__(self, skills_dir: str = None):
        if skills_dir is None:
            # Versuche mehrere Pfade
            candidates = [
                Path.home() / ".wissenschaft" / "skills",
                Path.home() / "HAUPTLAGER" / "03_PROJEKTE" / "XX_WissenschaftSkill" / "skills" / "domains",
            ]
            for c in candidates:
                if c.exists():
                    self.dir = c
                    break
            else:
                self.dir = candidates[0]
        else:
            self.dir = Path(skills_dir).expanduser()
    
    def load_all(self) -> list[Skill]:
        """Lädt alle SKILL.md-Dateien rekursiv."""
        skills = []
        if not self.dir.exists():
            return skills
        
        for skill_file in self.dir.rglob("SKILL.md"):
            try:
                skill = self._parse_skill(skill_file)
                if skill:
                    skills.append(skill)
            except Exception as e:
                print(f"⚠️ Fehler beim Laden von {skill_file}: {e}")
        
        return skills
    
    def _parse_skill(self, filepath: Path) -> Skill | None:
        """Parst eine SKILL.md-Datei."""
        content = filepath.read_text(encoding='utf-8')
        
        # YAML-Frontmatter extrahieren
        frontmatter = {}
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                except yaml.YAMLError:
                    pass
        
        name = frontmatter.get('name', filepath.parent.name)
        domain = frontmatter.get('domain', filepath.parent.name)
        triggers = frontmatter.get('triggers', [])
        sources = frontmatter.get('sources', [])
        
        if not sources:
            return None
        
        return Skill(
            name=name,
            domain=domain,
            triggers=triggers,
            sources=sources,
            path=str(filepath),
        )
    
    def get_triggers_map(self) -> dict:
        """{trigger_word: [skill_names]}"""
        tmap = {}
        for skill in self.load_all():
            for trigger in skill.triggers:
                tmap.setdefault(trigger.lower(), []).append(skill.name)
        return tmap


class SkillEngine:
    """Matcht Queries auf Skills und löst Quellen auf."""
    
    def __init__(self, loader: SkillLoader = None):
        self.loader = loader or SkillLoader()
        self.skills = self.loader.load_all()
        self.triggers = self.loader.get_triggers_map()
    
    def match(self, query: str, domain: str = None) -> list[Skill]:
        """Findet passende Skills für Query + Domain."""
        matched = []
        query_lower = query.lower()
        
        for skill in self.skills:
            score = 0
            
            # Domain-Match
            if domain and skill.domain == domain:
                score += 3
            
            # Trigger-Match
            for trigger in skill.triggers:
                if re.search(r'\b' + re.escape(trigger.lower()) + r'\b', query_lower):
                    score += 2
            
            if score > 0:
                matched.append((score, skill))
        
        matched.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in matched]
    
    def resolve_sources(self, skills: list[Skill]) -> list[dict]:
        """Löst Skill-Quellen in API-Call-Definitionen auf."""
        sources = []
        for skill in skills:
            for src in skill.sources:
                sources.append({
                    "name": src.get("name", "?"),
                    "type": src.get("type", "mcp"),
                    "tool": src.get("tool", ""),
                    "endpoint": src.get("endpoint", ""),
                    "query_template": src.get("query_template", "{query}"),
                    "max_results": src.get("max_results", 10),
                    "domain": skill.domain,
                    "skill_name": skill.name,
                })
        return sources


class SkillValidator:
    """Validiert SKILL.md-Dateien."""
    
    REQUIRED_FIELDS = ['name', 'domain', 'triggers', 'sources']
    
    def validate(self, filepath: str) -> dict:
        """Prüft ob SKILL.md gültig ist. Returns {valid, errors, warnings}."""
        errors = []
        warnings = []
        
        path = Path(filepath)
        if not path.exists():
            return {"valid": False, "errors": ["Datei nicht gefunden"], "warnings": []}
        
        content = path.read_text(encoding='utf-8')
        
        # YAML-Frontmatter
        if not content.startswith('---'):
            errors.append("Kein YAML-Frontmatter (---)")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        parts = content.split('---', 2)
        if len(parts) < 3:
            errors.append("Frontmatter nicht geschlossen")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        try:
            fm = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError as e:
            errors.append(f"YAML-Fehler: {e}")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        # Pflichtfelder
        for field in self.REQUIRED_FIELDS:
            if field not in fm:
                errors.append(f"Pflichtfeld '{field}' fehlt")
        
        if 'sources' in fm and not fm['sources']:
            warnings.append("Keine Quellen definiert")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

if __name__ == "__main__":
    loader = SkillLoader()
    skills = loader.load_all()
    print(f"Skills geladen: {len(skills)}")
    
    engine = SkillEngine(loader)
    matched = engine.match("trading FVG microstructure")
    print(f"Gematcht: {len(matched)} Skills")
    for s in matched:
        print(f"  - {s.name} ({s.domain}): {len(s.sources)} Quellen")
