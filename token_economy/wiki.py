from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


WIKI_DIRS = ("raw", "concepts", "patterns", "projects", "people", "queries", "L2_facts", "L3_sops", "L4_archive")
SKIP_PARTS = {".git", ".token-economy", "__pycache__", ".pytest_cache"}
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
V2_REQUIRED = ("title", "type", "domain", "tier", "confidence", "created", "updated", "verified", "sources", "supersedes", "superseded-by", "tags")
V2_TYPES = {"entity", "summary", "decision", "source-summary", "procedure", "concept", "pattern", "project", "query", "fact", "sop", "raw", "person", "handoff"}
V2_TIERS = {"working", "episodic", "semantic", "procedural"}


DEFAULT_SCHEMA = """# Token Economy Wiki Schema

Purpose: a repo-local markdown LLM wiki for durable agent memory.

## Layers
- `raw/`: immutable sources. Never rewrite.
- `concepts/`, `patterns/`, `projects/`, `people/`, `queries/`: synthesized pages.
- `index.md`: compact catalog. Read first.
- `log.md`: append-only operation timeline.
- `L0_rules.md`: stable rules loaded at startup.
- `L1_index.md`: compact pointer index loaded at startup.
- `L2_facts/`: verified durable facts.
- `L3_sops/`: solved-task playbooks.
- `L4_archive/`: cold session archives.

## Frontmatter v2 for new pages
```yaml
---
schema_version: 2
title: Example
type: entity|summary|decision|source-summary|procedure|concept|pattern|project|query|fact|sop|raw|person|handoff
domain: framework|tools|patterns|experiments|project
tier: working|episodic|semantic|procedural
confidence: 0.0
created: YYYY-MM-DD
updated: YYYY-MM-DD
verified: YYYY-MM-DD
sources: []
supersedes: []
superseded-by:
tags: []
---
```

Legacy v1 pages remain readable. Strict lint emits migration warnings for v1 pages and enforces v2 fields on v2/template-generated pages.

## Workflows
- Ingest: source -> `raw/` note -> update synthesized pages -> backlinks -> `index.md`/`log.md`.
- Query: search -> timeline -> fetch only relevant pages -> cite paths -> optionally file answer in `queries/`.
- Lint: stale claims, orphan pages, broken links, contradictions, supersession candidates.
- Crystallize: successful verified work -> `L3_sops/` and durable lessons.
"""


@dataclass
class Page:
    id: str
    path: Path
    title: str
    type: str
    tags: list[str]
    preview: str
    body: str
    links: list[str]
    frontmatter: dict[str, str]


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return slug or "note"


def page_id(root: Path, path: Path) -> str:
    return path.relative_to(root).with_suffix("").as_posix()


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text
    raw = text[4:end].strip()
    body = text[end + 4 :].lstrip("\n")
    fm: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fm[key.strip()] = value.strip().strip("\"'")
    return fm, body


def parse_tags(value: str) -> list[str]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        return [x.strip().strip("\"'") for x in value[1:-1].split(",") if x.strip()]
    if not value:
        return []
    return [value]


def strip_fenced_code(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def normalize_wikilink(inner: str) -> str:
    target = inner.strip().split("|", 1)[0].split("#", 1)[0].strip()
    return target.rstrip("\\").removesuffix(".md")


def is_v2_page(fm: dict[str, str]) -> bool:
    return fm.get("schema_version") == "2" or all(key in fm for key in ("title", "domain", "tier", "sources"))


def confidence_value(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        legacy = {"low": 0.25, "med": 0.6, "medium": 0.6, "high": 0.9}
        return legacy.get(str(value).strip().lower())


def render_template(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


class WikiStore:
    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()
        self.state_dir = self.root / ".token-economy"
        self.db_path = self.state_dir / "wiki.sqlite3"

    def init(self) -> dict[str, Any]:
        self.root.mkdir(parents=True, exist_ok=True)
        for name in WIKI_DIRS:
            (self.root / name).mkdir(parents=True, exist_ok=True)
        created = []
        templates = {
            "index.md": "# Wiki Index\n\nCompact catalog. Update after material wiki changes.\n",
            "log.md": "# Wiki Log\n\n",
            "schema.md": DEFAULT_SCHEMA,
            "L0_rules.md": "# L0 Rules\n\n- Caveman Ultra by default.\n- Retrieve before reasoning about stored facts.\n",
            "L1_index.md": "# L1 Index\n\nRun `./te wiki index` to rebuild pointers.\n",
        }
        for rel, content in templates.items():
            path = self.root / rel
            if not path.exists():
                path.write_text(content, encoding="utf-8")
                created.append(rel)
        self.state_dir.mkdir(exist_ok=True)
        return {"wiki_root": str(self.root), "created": created}

    def iter_markdown(self) -> list[Path]:
        files = []
        for path in self.root.rglob("*.md"):
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            files.append(path)
        return sorted(files)

    def read_page(self, path: Path) -> Page:
        text = path.read_text(encoding="utf-8", errors="replace")
        fm, body = parse_frontmatter(text)
        title = ""
        for line in body.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        title = title or path.stem.replace("-", " ").replace("_", " ").title()
        preview = ""
        for line in body.splitlines():
            clean = line.strip()
            if clean and not clean.startswith("#"):
                preview = clean[:240]
                break
        links = [normalize_wikilink(x) for x in WIKILINK_RE.findall(strip_fenced_code(body))]
        return Page(
            id=page_id(self.root, path),
            path=path,
            title=title,
            type=fm.get("type", ""),
            tags=parse_tags(fm.get("tags", "")),
            preview=preview,
            body=body,
            links=links,
            frontmatter=fm,
        )

    def pages(self) -> list[Page]:
        return [self.read_page(path) for path in self.iter_markdown()]

    def index(self) -> dict[str, Any]:
        self.init()
        pages = self.pages()
        self.state_dir.mkdir(exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DROP TABLE IF EXISTS docs")
            conn.execute("DROP TABLE IF EXISTS docs_fts")
            conn.execute(
                "CREATE TABLE docs (id TEXT PRIMARY KEY, path TEXT, title TEXT, type TEXT, tags TEXT, preview TEXT, body TEXT, links TEXT, mtime REAL)"
            )
            fts_enabled = True
            try:
                conn.execute("CREATE VIRTUAL TABLE docs_fts USING fts5(id, title, body, tags)")
            except sqlite3.OperationalError:
                fts_enabled = False
            for page in pages:
                tags = ",".join(page.tags)
                conn.execute(
                    "INSERT INTO docs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        page.id,
                        page.path.relative_to(self.root).as_posix(),
                        page.title,
                        page.type,
                        tags,
                        page.preview,
                        page.body,
                        json.dumps(page.links),
                        page.path.stat().st_mtime,
                    ),
                )
                if fts_enabled:
                    conn.execute("INSERT INTO docs_fts VALUES (?, ?, ?, ?)", (page.id, page.title, page.body, tags))
        l1_lines = [
            "# L1 Index",
            "",
            "Compact pointers. Fetch details on demand.",
            "",
            "- start -> `start.md`",
            "- config -> `token-economy.yaml`",
            "- model registry -> `models.yaml`",
            "- L0 rules -> `L0_rules.md`",
            "- schema -> `schema.md`",
            "- wiki catalog -> `index.md`",
            "- log -> `log.md`",
            "- raw sources -> `raw/` (search only; fetch after relevance)",
        ]
        priority = {
            "start",
            "README",
            "AGENT_ONBOARDING",
            "ROADMAP",
            "stable/README",
            "projects/wiki-search/README",
            "projects/context-refresh/README",
            "projects/context-keeper-v2/README",
            "projects/delegate-router/README",
            "projects/compound-compression-pipeline/RESULTS",
            "projects/semdiff/README",
        }
        l1_support_dirs = {"templates", "skills", "prompts", "hooks", "configs", "adapters"}
        ordered = sorted(pages, key=lambda p: (0 if p.id in priority else 1, p.id))
        seen_l1 = {
            "start",
            "config",
            "model registry",
            "L0 rules",
            "schema",
            "wiki catalog",
            "log",
            "raw sources",
            "L0_rules",
            "L1_index",
            "index",
            "AGENTS",
            "CLAUDE",
            "GEMINI",
        }
        for page in ordered:
            if len(l1_lines) >= 45:
                break
            if page.id in seen_l1:
                continue
            parts = set(Path(page.id).parts)
            if parts & l1_support_dirs:
                continue
            if page.id.startswith("extensions/") and page.id != "extensions/README":
                continue
            if page.id.startswith("raw/"):
                continue
            if page.id in {"external-adapters"}:
                continue
            if page.id.endswith("/INSTALL") or "/agents/" in page.id or "/kaggle_results/" in page.id:
                continue
            tags = f" tags={','.join(page.tags)}" if page.tags else ""
            l1_lines.append(f"- {page.id} ({page.type or 'page'}{tags}) -> `{page.path.relative_to(self.root).as_posix()}`")
            seen_l1.add(page.id)
        (self.root / "L1_index.md").write_text("\n".join(l1_lines) + "\n", encoding="utf-8")
        return {"indexed": len(pages), "db": str(self.db_path), "fts5": fts_enabled}

    def _ensure_db(self) -> None:
        if not self.db_path.exists():
            self.index()

    def search(self, query: str, k: int = 10) -> list[dict[str, Any]]:
        self._ensure_db()
        tokens = re.findall(r"[A-Za-z0-9_/-]+", query)
        fts_query = " OR ".join(tokens) if tokens else query
        rows: list[tuple[Any, ...]]
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            try:
                rows = conn.execute(
                    """
                    SELECT docs.id, docs.path, docs.title, docs.type, docs.tags, docs.preview, bm25(docs_fts) AS score
                    FROM docs_fts JOIN docs ON docs_fts.id = docs.id
                    WHERE docs_fts MATCH ?
                    ORDER BY score LIMIT ?
                    """,
                    (fts_query, k),
                ).fetchall()
            except sqlite3.Error:
                like = f"%{query}%"
                rows = conn.execute(
                    """
                    SELECT id, path, title, type, tags, preview, 0 AS score
                    FROM docs
                    WHERE title LIKE ? OR body LIKE ? OR tags LIKE ?
                    LIMIT ?
                    """,
                    (like, like, like, k),
                ).fetchall()
        return [
            {
                "id": row["id"],
                "path": row["path"],
                "title": row["title"],
                "type": row["type"],
                "tags": [x for x in str(row["tags"]).split(",") if x],
                "preview": row["preview"],
                "score": row["score"],
            }
            for row in rows
        ]

    def fetch(self, item_id: str) -> dict[str, Any]:
        self._ensure_db()
        key = item_id.removesuffix(".md")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM docs WHERE id = ? OR path = ?", (key, item_id)).fetchone()
        if not row:
            raise KeyError(f"wiki page not found: {item_id}")
        return {
            "id": row["id"],
            "path": row["path"],
            "title": row["title"],
            "type": row["type"],
            "tags": [x for x in str(row["tags"]).split(",") if x],
            "content": row["body"],
        }

    def timeline(self, item_id: str, window: int = 3) -> dict[str, Any]:
        page = self.fetch(item_id)
        pages = self.pages()
        target_id = page["id"]
        target_title = page["title"]
        backlinks = []
        neighbors = []
        same_dir = []
        for p in pages:
            if target_id in p.links or target_title in p.links:
                backlinks.append({"id": p.id, "title": p.title, "path": p.path.relative_to(self.root).as_posix()})
            if str(p.path.parent) == str((self.root / page["path"]).parent):
                same_dir.append(p)
        same_dir = sorted(same_dir, key=lambda p: p.path.as_posix())
        ids = [p.id for p in same_dir]
        if target_id in ids:
            idx = ids.index(target_id)
            for p in same_dir[max(0, idx - window) : idx + window + 1]:
                if p.id != target_id:
                    neighbors.append({"id": p.id, "title": p.title, "path": p.path.relative_to(self.root).as_posix()})
        log_hits = []
        log_path = self.root / "log.md"
        if log_path.exists():
            for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
                if target_id in line or target_title in line:
                    log_hits.append(line[:240])
        return {"id": target_id, "backlinks": backlinks[:20], "neighbors": neighbors[:20], "log": log_hits[-10:]}

    def lint(self) -> dict[str, Any]:
        return self.lint_pages(strict=False)

    def lint_pages(self, strict: bool = False) -> dict[str, Any]:
        pages = self.pages()
        ids = {p.id for p in pages}
        stems = {Path(p.id).name for p in pages}
        incoming: dict[str, int] = {p.id: 0 for p in pages}
        broken = []
        missing_frontmatter = []
        supersession = []
        errors = []
        warnings = []
        for p in pages:
            rel_parts = set(p.path.relative_to(self.root).parts)
            if strict and rel_parts & {"templates", "skills", "prompts", "hooks", "configs", "extensions", "adapters"}:
                continue
            if p.path.name not in {"index.md", "log.md", "schema.md", "L0_rules.md", "L1_index.md"} and not p.frontmatter:
                missing_frontmatter.append(p.id)
                if strict:
                    warnings.append({"code": "legacy_missing_frontmatter", "page": p.id})
            if "supersedes" in p.frontmatter or "superseded-by" in p.frontmatter:
                supersession.append(p.id)
            if strict:
                if is_v2_page(p.frontmatter):
                    self._lint_v2_page(p, ids, stems, errors, warnings)
                elif p.frontmatter and p.path.name not in {"index.md", "log.md", "schema.md", "L0_rules.md", "L1_index.md"}:
                    warnings.append({"code": "legacy_frontmatter_v1", "page": p.id})
                if p.id.startswith("raw/") and p.frontmatter.get("type") not in {"raw", "source-summary"}:
                    warnings.append({"code": "raw_type_not_raw", "page": p.id})
            for link in p.links:
                link_id = link.removesuffix(".md")
                if link_id in incoming:
                    incoming[link_id] += 1
                elif link_id not in ids and Path(link_id).name not in stems:
                    broken.append({"from": p.id, "to": link})
                    if strict and is_v2_page(p.frontmatter):
                        errors.append({"code": "broken_link", "page": p.id, "target": link})
        exempt = {"index", "log", "schema", "L0_rules", "L1_index", "README", "start"}
        support_dirs = {"templates", "skills", "prompts", "hooks", "configs", "extensions", "adapters"}
        orphans = [
            pid
            for pid, count in incoming.items()
            if count == 0
            and Path(pid).name not in exempt
            and not pid.startswith("raw/")
            and not (set(Path(pid).parts) & support_dirs)
        ]
        if strict:
            for pid in orphans:
                page = next((p for p in pages if p.id == pid), None)
                if page and is_v2_page(page.frontmatter):
                    warnings.append({"code": "orphan", "page": pid})
        result = {
            "pages": len(pages),
            "missing_frontmatter": missing_frontmatter,
            "broken_links": broken,
            "orphans": orphans,
            "supersession_candidates": supersession,
        }
        if strict:
            result["strict"] = True
            result["errors"] = errors
            result["warnings"] = warnings
            result["ok"] = not errors
        return result

    def _lint_v2_page(self, page: Page, ids: set[str], stems: set[str], errors: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> None:
        fm = page.frontmatter
        for key in V2_REQUIRED:
            if key not in fm:
                errors.append({"code": "missing_v2_field", "page": page.id, "field": key})
        if fm.get("type") and fm["type"] not in V2_TYPES:
            errors.append({"code": "invalid_type", "page": page.id, "value": fm["type"]})
        if fm.get("tier") and fm["tier"] not in V2_TIERS:
            errors.append({"code": "invalid_tier", "page": page.id, "value": fm["tier"]})
        conf = confidence_value(fm.get("confidence", ""))
        if conf is None or conf < 0.0 or conf > 1.0:
            errors.append({"code": "invalid_confidence", "page": page.id, "value": fm.get("confidence", "")})
        for key in ("created", "updated", "verified"):
            value = fm.get(key, "")
            if value:
                try:
                    parsed = date.fromisoformat(value)
                    if key == "verified" and (date.today() - parsed).days > 180:
                        warnings.append({"code": "stale_verified", "page": page.id, "verified": value})
                except ValueError:
                    errors.append({"code": "invalid_date", "page": page.id, "field": key, "value": value})
        for key in ("supersedes", "superseded-by"):
            value = fm.get(key, "")
            for target in re.findall(r"\[\[([^\]]+)\]\]", value):
                target_id = target.removesuffix(".md")
                if target_id not in ids and Path(target_id).name not in stems:
                    errors.append({"code": "broken_supersession", "page": page.id, "target": target})

    def new_page(self, template: str, title: str, domain: str = "framework", slug: str | None = None) -> dict[str, Any]:
        self.init()
        template_map = {
            "page": ("templates/page.template.md", "concepts"),
            "decision": ("templates/decision.template.md", "queries"),
            "source-summary": ("templates/source-summary.template.md", "raw"),
        }
        if template not in template_map:
            raise KeyError(f"unknown template: {template}")
        template_rel, target_dir = template_map[template]
        template_path = self.root / template_rel
        if not template_path.exists():
            template_path = Path(__file__).resolve().parents[1] / template_rel
        content_template = template_path.read_text(encoding="utf-8")
        today = date.today().isoformat()
        page_slug = slugify(slug or title)
        filename = f"{today}-{page_slug}.md" if target_dir == "raw" else f"{page_slug}.md"
        target = self.root / target_dir / filename
        if target.exists():
            raise FileExistsError(target)
        content = render_template(
            content_template,
            {
                "title": title,
                "domain": domain,
                "date": today,
            },
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        self.append_log("update", title, f"Created `{target.relative_to(self.root).as_posix()}` from `{template}` template.")
        self.index()
        return {"created": target.relative_to(self.root).as_posix(), "template": template, "title": title}

    def ingest(self, source: str, title: str | None = None) -> dict[str, Any]:
        self.init()
        today = date.today().isoformat()
        source_path = Path(source).expanduser()
        is_file = source_path.exists()
        note_title = title or (source_path.stem if is_file else source)
        slug = slugify(note_title)
        target = self.root / "raw" / f"{today}-{slug}.md"
        i = 2
        while target.exists():
            target = self.root / "raw" / f"{today}-{slug}-{i}.md"
            i += 1
        if is_file:
            body = source_path.read_text(encoding="utf-8", errors="replace")
            source_ref = source_path.as_posix()
        else:
            body = f"Source URL: {source}\n"
            source_ref = source
        safe_title = note_title.replace('"', '\\"')
        safe_source = source_ref.replace('"', '\\"')
        content = (
            "---\n"
            "schema_version: 2\n"
            f"title: \"{safe_title}\"\n"
            "type: raw\n"
            "domain: external-source\n"
            "tier: episodic\n"
            "confidence: 0.6\n"
            f"created: {today}\n"
            f"updated: {today}\n"
            f"verified: {today}\n"
            f"sources: [\"{safe_source}\"]\n"
            "supersedes: []\n"
            "superseded-by:\n"
            "tags: [ingest, raw]\n"
            "---\n\n"
            f"# {note_title}\n\n"
            f"{body}\n"
        )
        target.write_text(content, encoding="utf-8")
        self.append_log("ingest", note_title, f"Added raw source `{target.relative_to(self.root).as_posix()}`.")
        index_result = self.index()
        return {"created": target.relative_to(self.root).as_posix(), "indexed": index_result["indexed"]}

    def append_log(self, op: str, title: str, body: str) -> None:
        log_path = self.root / "log.md"
        if not log_path.exists():
            log_path.write_text("# Wiki Log\n\n", encoding="utf-8")
        entry = f"## [{date.today().isoformat()}] {op} | {title}\n\n{body}\n\n"
        with log_path.open("a", encoding="utf-8") as f:
            f.write(entry)
