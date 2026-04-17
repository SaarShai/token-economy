"""AST extraction + diff. Language-agnostic via tree-sitter."""
from __future__ import annotations
import hashlib
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

warnings.filterwarnings("ignore", category=FutureWarning)
from tree_sitter_languages import get_parser

# Language-specific node types to extract. (type, name_field)
# name_field is the child field whose text gives the node's identifier.
LANG_NODES = {
    "python": {
        "function_definition": "name",
        "class_definition": "name",
    },
    "javascript": {
        "function_declaration": "name",
        "method_definition": "name",
        "class_declaration": "name",
    },
    "typescript": {
        "function_declaration": "name",
        "method_definition": "name",
        "class_declaration": "name",
        "interface_declaration": "name",
    },
    "rust": {
        "function_item": "name",
        "struct_item": "name",
        "enum_item": "name",
        "trait_item": "name",
        "impl_item": None,   # name derived from type
    },
}

EXT_LANG = {
    ".py": "python",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript",
    ".ts": "typescript", ".tsx": "typescript",
    ".rs": "rust",
}


@dataclass
class Node:
    name: str          # fully-qualified name e.g. "ClassName.method"
    kind: str          # tree-sitter node type
    start: int         # byte offset
    end: int
    source: bytes
    hash: str
    line_start: int    # 1-indexed
    line_end: int


def detect_lang(path: str | Path) -> Optional[str]:
    return EXT_LANG.get(Path(path).suffix.lower())


def _node_name(node, source: bytes, kind_map) -> Optional[str]:
    """Best-effort name from a tree-sitter node."""
    field = kind_map.get(node.type)
    if field is None:
        # Rust impl: name = "impl <type>"
        if node.type == "impl_item":
            ty = node.child_by_field_name("type")
            if ty:
                return "impl_" + source[ty.start_byte:ty.end_byte].decode("utf-8", "replace")
        return None
    child = node.child_by_field_name(field)
    if child is None:
        return None
    return source[child.start_byte:child.end_byte].decode("utf-8", "replace")


def extract_nodes(source: bytes, lang: str) -> list[Node]:
    """Walk AST, extract top-level + nested definitions with qualified names."""
    parser = get_parser(lang)
    tree = parser.parse(source)
    kind_map = LANG_NODES[lang]
    out: list[Node] = []

    def walk(ts_node, prefix: str):
        for child in ts_node.children:
            if child.type in kind_map:
                nm = _node_name(child, source, kind_map)
                if nm:
                    qname = f"{prefix}{nm}" if prefix else nm
                    body = source[child.start_byte:child.end_byte]
                    h = hashlib.sha1(body).hexdigest()[:12]
                    out.append(Node(
                        name=qname, kind=child.type,
                        start=child.start_byte, end=child.end_byte,
                        source=body, hash=h,
                        line_start=child.start_point[0] + 1,
                        line_end=child.end_point[0] + 1,
                    ))
                    # recurse into class/impl bodies for methods
                    body_node = child.child_by_field_name("body")
                    if body_node:
                        walk(body_node, f"{qname}.")
                    continue
            walk(child, prefix)

    walk(tree.root_node, "")
    return out


def snapshot(path: str | Path) -> dict[str, str]:
    """{qualified_name → hash} for a file. Used for diff baseline."""
    path = Path(path)
    lang = detect_lang(path)
    if not lang:
        raise ValueError(f"unsupported extension: {path.suffix}")
    source = path.read_bytes()
    nodes = extract_nodes(source, lang)
    return {n.name: n.hash for n in nodes}


def render_diff(path: str | Path, prev: dict[str, str]) -> tuple[str, dict]:
    """Compare current file vs prev snapshot; render diff view.

    Returns (rendered_text, metadata).
    metadata has: added, removed, changed, unchanged (lists of names).
    """
    path = Path(path)
    lang = detect_lang(path)
    source = path.read_bytes()
    nodes = extract_nodes(source, lang)
    curr = {n.name: n.hash for n in nodes}
    by_name = {n.name: n for n in nodes}

    added = [n for n in curr if n not in prev]
    removed = [n for n in prev if n not in curr]
    changed = [n for n in curr if n in prev and curr[n] != prev[n]]
    unchanged = [n for n in curr if n in prev and curr[n] == prev[n]]

    lines = [f"// semdiff: {path} (lang={lang}, diff-since-last-read)"]
    lines.append(f"// summary: +{len(added)} ~{len(changed)} -{len(removed)} ={len(unchanged)}")
    lines.append("")

    for nm in removed:
        lines.append(f"// [removed: {nm}]")
    if removed:
        lines.append("")

    # emit changed + added in file order
    emit_set = set(changed) | set(added)
    # Dedupe parent/child: if a child is in emit_set, drop the parent (class/impl)
    # since we'd re-emit its children anyway.
    child_parents = {n.rsplit(".", 1)[0] for n in emit_set if "." in n}
    # For each parent in emit_set, check if we have any children — if so, skip parent unless it's only the header that changed
    def skip_parent(name):
        # skip if any other emit node has this name as prefix
        pref = name + "."
        return any(other != name and other.startswith(pref) for other in emit_set)
    emit_set = {n for n in emit_set if not skip_parent(n)}
    emit = [n for n in nodes if n.name in emit_set]
    emit.sort(key=lambda n: n.start)

    unchanged_set = set(unchanged)
    emitted_unchanged_stub = False

    last_end_line = 0
    for n in emit:
        # Stub unchanged nodes between last and this one
        between = [u for u in nodes
                   if u.name in unchanged_set
                   and u.start < n.start
                   and u.line_start > last_end_line]
        if between:
            names = [u.name for u in between[:5]]
            more = len(between) - 5
            stub = ", ".join(names) + (f", +{more} more" if more > 0 else "")
            lines.append(f"// [unchanged: {stub}]")
            lines.append("")

        tag = "ADDED" if n.name in added else "CHANGED"
        lines.append(f"// --- {tag}: {n.name} (L{n.line_start}-{n.line_end}) ---")
        lines.append(n.source.decode("utf-8", "replace"))
        lines.append("")
        last_end_line = n.line_end

    # trailing unchanged stub
    trailing = [u for u in nodes if u.name in unchanged_set and u.line_start > last_end_line]
    if trailing:
        names = [u.name for u in trailing[:5]]
        more = len(trailing) - 5
        stub = ", ".join(names) + (f", +{more} more" if more > 0 else "")
        lines.append(f"// [unchanged: {stub}]")

    meta = {
        "added": added, "removed": removed,
        "changed": changed, "unchanged": unchanged,
        "lang": lang, "node_count": len(nodes),
    }
    return "\n".join(lines), meta


def read_smart(path: str | Path, session_id: str, cache_dir: Optional[Path] = None) -> tuple[str, dict]:
    """Main entry. First read: return full file + store snapshot.
    Subsequent: return diff view.
    """
    from .cache import SessionCache
    path = Path(path).resolve()
    cache = SessionCache(session_id, cache_dir=cache_dir)
    prev = cache.get(str(path))

    if prev is None:
        source = path.read_bytes().decode("utf-8", "replace")
        cache.set(str(path), snapshot(path))
        return source, {"mode": "full", "reason": "first-read"}

    rendered, meta = render_diff(path, prev)
    # update snapshot
    cache.set(str(path), {n: h for n, h in [(k, prev[k]) for k in meta["unchanged"]]
                           + [(k, snapshot(path)[k]) for k in meta["changed"] + meta["added"]]})
    meta["mode"] = "diff"
    return rendered, meta
