from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from .config import detect_agent, load_config
from .bench import run_framework_smoke
from .context import checkpoint, fresh_launch_commands, host_context_controls, lint_handoff, meter, status_for_files
from .delegate import delegation_plan, dumps, load_models, classify, personal_assistant_directive, personal_assistant_packet
from .docs import audit as docs_audit, split_plan
from .hooks import doctor as hooks_doctor
from .profile import set_profile, show as show_profile
from .tokens import estimate_tokens
from .wiki import WikiStore


def print_json(obj: Any) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def cmd_doctor(args: argparse.Namespace) -> int:
    cfg = load_config(args.repo)
    checks = {
        "repo_root": str(cfg.repo_root),
        "config": (cfg.repo_root / "token-economy.yaml").exists(),
        "start_md": (cfg.repo_root / "start.md").exists(),
        "wiki_root": str(cfg.wiki_root),
        "wiki_root_exists": cfg.wiki_root.exists(),
        "refresh_threshold": cfg.refresh_threshold,
        "comcom_mcp": (cfg.repo_root / "projects/compound-compression-pipeline/comcom_mcp/server.py").exists(),
        "semdiff_mcp": (cfg.repo_root / "projects/semdiff/semdiff_mcp/server.py").exists(),
        "context_keeper": (cfg.repo_root / "projects/context-keeper").exists(),
        "python": sys.version.split()[0],
    }
    checks["ok"] = all(v for k, v in checks.items() if k not in {"repo_root", "wiki_root", "refresh_threshold", "python"})
    print_json(checks)
    return 0 if checks["ok"] else 1


def adapter_target(repo_root: Path, agent: str) -> Path:
    if agent == "claude":
        return repo_root / "CLAUDE.md"
    if agent == "gemini":
        return repo_root / "GEMINI.md"
    if agent == "cursor":
        return repo_root / ".cursor" / "rules" / "token-economy.mdc"
    return repo_root / "AGENTS.md"


def cmd_start(args: argparse.Namespace) -> int:
    cfg = load_config(args.repo)
    if args.scope != "project":
        raise SystemExit("Token Economy installs project-locally only; use --scope project.")
    agent = detect_agent() if args.agent == "auto" else args.agent
    src_name = "token-economy.mdc" if agent == "cursor" else {"claude": "CLAUDE.md", "gemini": "GEMINI.md"}.get(agent, "AGENTS.md")
    src = cfg.repo_root / "adapters" / agent / src_name
    if not src.exists():
        raise SystemExit(f"unknown adapter: {agent}")
    target = adapter_target(cfg.repo_root, agent)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and "Token Economy Adapter" not in target.read_text(encoding="utf-8", errors="replace"):
        sidecar = target.with_name(target.name + ".token-economy")
        shutil.copyfile(src, sidecar)
        print_json({"agent": agent, "scope": args.scope, "installed": str(sidecar), "note": f"existing {target.name} left untouched"})
        return 0
    shutil.copyfile(src, target)
    print_json({"agent": agent, "scope": args.scope, "installed": str(target)})
    return 0


def cmd_wiki(args: argparse.Namespace) -> int:
    cfg = load_config(args.repo)
    wiki = WikiStore(cfg.wiki_root)
    if args.wiki_cmd == "init":
        print_json(wiki.init())
    elif args.wiki_cmd == "index":
        print_json(wiki.index())
    elif args.wiki_cmd == "search":
        print_json(wiki.search(args.query, args.k))
    elif args.wiki_cmd == "fetch":
        print_json(wiki.fetch(args.id))
    elif args.wiki_cmd == "timeline":
        print_json(wiki.timeline(args.id, args.window))
    elif args.wiki_cmd == "lint":
        result = wiki.lint_pages(strict=args.strict)
        print_json(result)
        if args.fail_on_error and result.get("errors"):
            return 1
    elif args.wiki_cmd == "ingest":
        print_json(wiki.ingest(args.source, args.title))
    elif args.wiki_cmd == "new":
        print_json(wiki.new_page(args.template, args.title, args.domain, args.slug))
    elif args.wiki_cmd == "query":
        hits = wiki.search(args.query, args.k)
        print_json({"query": args.query, "hits": hits, "next": "Use `te wiki timeline <id>` then `te wiki fetch <id>` for relevant hits only."})
    return 0


def cmd_docs(args: argparse.Namespace) -> int:
    cfg = load_config(args.repo)
    if args.docs_cmd == "audit":
        print_json(docs_audit(cfg.repo_root, args.limit))
    elif args.docs_cmd == "split":
        path = Path(args.path)
        if not path.is_absolute():
            path = cfg.repo_root / path
        print_json(split_plan(cfg.repo_root, path))
    elif args.docs_cmd == "load":
        path = Path(args.path)
        if not path.is_absolute():
            path = cfg.repo_root / path
        text = path.read_text(encoding="utf-8", errors="replace")
        print(text)
    return 0


def cmd_context(args: argparse.Namespace) -> int:
    cfg = load_config(args.repo)
    if args.context_cmd == "status":
        files = [cfg.repo_root / "start.md"]
        for rel in ("L0_rules.md", "L1_index.md"):
            files.append(cfg.wiki_root / rel)
        result = status_for_files(files, cfg.context_max_tokens, cfg.refresh_threshold)
        print_json(result)
    elif args.context_cmd == "meter":
        transcript = Path(args.transcript).expanduser() if args.transcript else None
        print_json(meter(transcript=transcript, model=args.model, max_tokens=cfg.context_max_tokens))
    elif args.context_cmd == "checkpoint":
        transcript = Path(args.transcript).expanduser() if args.transcript else None
        context_pct = "unknown"
        if transcript and transcript.exists():
            context_pct = str(meter(transcript=transcript, max_tokens=cfg.context_max_tokens)["pct"])
        result = checkpoint(cfg.repo_root, goal=args.goal or "", plan=args.plan or "", transcript=transcript, max_packet_tokens=args.max_tokens, context_pct=context_pct)
        if args.print_packet:
            print(result["packet"])
        else:
            print_json({k: v for k, v in result.items() if k != "packet"})
    elif args.context_cmd == "fresh-start":
        result = checkpoint(cfg.repo_root, goal=args.goal or "", plan=args.plan or "", max_packet_tokens=args.max_tokens)
        print(result["packet"])
        print(f"\nFresh packet written: {result['path']}")
        print("Open a fresh session with this packet if the host cannot clear context programmatically.")
    elif args.context_cmd == "lint-handoff":
        print_json(lint_handoff(Path(args.path).expanduser(), max_tokens=args.max_tokens))
    elif args.context_cmd == "host-controls":
        agent = detect_agent() if args.agent == "auto" else args.agent
        print_json(host_context_controls(agent))
    elif args.context_cmd == "fresh-command":
        agent = detect_agent() if args.agent == "auto" else args.agent
        handoff = Path(args.handoff).expanduser() if args.handoff else None
        if handoff and not handoff.is_absolute():
            handoff = cfg.repo_root / handoff
        print_json(fresh_launch_commands(agent, cfg.repo_root, handoff))
    return 0


def cmd_delegate(args: argparse.Namespace) -> int:
    cfg = load_config(args.repo)
    registry = load_models(cfg.model_registry)
    if args.delegate_cmd == "models":
        print_json(registry)
    elif args.delegate_cmd == "classify":
        print(dumps(classify(args.task, registry).as_dict()))
    elif args.delegate_cmd == "plan":
        print_json(delegation_plan(args.task, registry))
    return 0


def cmd_pa(args: argparse.Namespace) -> int:
    cfg = load_config(args.repo)
    registry = load_models(cfg.model_registry)
    prompt = " ".join(args.prompt).strip()
    if not prompt:
        raise SystemExit("te pa requires a prompt, usually starting with /pa or /btw")
    packet = personal_assistant_packet(prompt, registry)
    if args.directive:
        print(personal_assistant_directive(packet))
    else:
        print_json(packet)
    return 0


def cmd_hooks(args: argparse.Namespace) -> int:
    cfg = load_config(args.repo)
    if args.hooks_cmd == "doctor":
        result = hooks_doctor(cfg.repo_root)
        print_json(result)
        return 0 if result["ok"] else 1
    return 0


def cmd_profile(args: argparse.Namespace) -> int:
    cfg = load_config(args.repo)
    if args.profile_cmd == "show":
        print_json(show_profile(cfg.repo_root))
    elif args.profile_cmd == "set":
        print_json(set_profile(cfg.repo_root, args.name))
    return 0


def cmd_bench(args: argparse.Namespace) -> int:
    cfg = load_config(args.repo)
    if args.bench_cmd == "run":
        if args.suite != "framework-smoke":
            raise SystemExit(f"unknown suite: {args.suite}")
        result = run_framework_smoke(cfg.repo_root)
        print_json(result)
        return 0 if result["ok"] else 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="te", description="Token Economy universal agent framework CLI")
    p.add_argument("--repo", default=None, help="Repo root or child path")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("doctor")
    d.set_defaults(func=cmd_doctor)

    s = sub.add_parser("start")
    s.add_argument("--agent", choices=["auto", "claude", "codex", "gemini", "cursor"], default="auto")
    s.add_argument("--scope", choices=["project"], default="project")
    s.set_defaults(func=cmd_start)

    w = sub.add_parser("wiki")
    wsub = w.add_subparsers(dest="wiki_cmd", required=True)
    wsub.add_parser("init").set_defaults(func=cmd_wiki)
    wsub.add_parser("index").set_defaults(func=cmd_wiki)
    ws = wsub.add_parser("search")
    ws.add_argument("query")
    ws.add_argument("-k", type=int, default=10)
    ws.set_defaults(func=cmd_wiki)
    wf = wsub.add_parser("fetch")
    wf.add_argument("id")
    wf.set_defaults(func=cmd_wiki)
    wt = wsub.add_parser("timeline")
    wt.add_argument("id")
    wt.add_argument("--window", type=int, default=3)
    wt.set_defaults(func=cmd_wiki)
    wl = wsub.add_parser("lint")
    wl.add_argument("--strict", action="store_true")
    wl.add_argument("--fail-on-error", action="store_true")
    wl.set_defaults(func=cmd_wiki)
    wi = wsub.add_parser("ingest")
    wi.add_argument("source")
    wi.add_argument("--title")
    wi.set_defaults(func=cmd_wiki)
    wn = wsub.add_parser("new")
    wn.add_argument("--template", choices=["page", "decision", "source-summary"], default="page")
    wn.add_argument("--title", required=True)
    wn.add_argument("--domain", default="framework")
    wn.add_argument("--slug")
    wn.set_defaults(func=cmd_wiki)
    wq = wsub.add_parser("query")
    wq.add_argument("query")
    wq.add_argument("-k", type=int, default=10)
    wq.set_defaults(func=cmd_wiki)

    docs = sub.add_parser("docs")
    dsub = docs.add_subparsers(dest="docs_cmd", required=True)
    da = dsub.add_parser("audit")
    da.add_argument("--limit", type=int, default=1500)
    da.set_defaults(func=cmd_docs)
    ds = dsub.add_parser("split")
    ds.add_argument("path")
    ds.set_defaults(func=cmd_docs)
    dl = dsub.add_parser("load")
    dl.add_argument("path")
    dl.set_defaults(func=cmd_docs)

    ctx = sub.add_parser("context")
    csub = ctx.add_subparsers(dest="context_cmd", required=True)
    csub.add_parser("status").set_defaults(func=cmd_context)
    cm = csub.add_parser("meter")
    cm.add_argument("--model", default="auto")
    cm.add_argument("--transcript")
    cm.set_defaults(func=cmd_context)
    cc = csub.add_parser("checkpoint")
    cc.add_argument("--goal")
    cc.add_argument("--plan")
    cc.add_argument("--transcript")
    cc.add_argument("--max-tokens", type=int, default=2000)
    cc.add_argument("--print-packet", action="store_true")
    cc.add_argument("--handoff-template", action="store_true")
    cc.set_defaults(func=cmd_context)
    cf = csub.add_parser("fresh-start")
    cf.add_argument("--goal")
    cf.add_argument("--plan")
    cf.add_argument("--max-tokens", type=int, default=2000)
    cf.set_defaults(func=cmd_context)
    cl = csub.add_parser("lint-handoff")
    cl.add_argument("path")
    cl.add_argument("--max-tokens", type=int, default=2000)
    cl.set_defaults(func=cmd_context)
    ch = csub.add_parser("host-controls")
    ch.add_argument("--agent", choices=["auto", "claude", "codex", "gemini", "cursor", "generic"], default="auto")
    ch.set_defaults(func=cmd_context)
    fc = csub.add_parser("fresh-command")
    fc.add_argument("--agent", choices=["auto", "claude", "codex", "gemini", "cursor", "generic"], default="auto")
    fc.add_argument("--handoff")
    fc.set_defaults(func=cmd_context)

    de = sub.add_parser("delegate")
    desub = de.add_subparsers(dest="delegate_cmd", required=True)
    desub.add_parser("models").set_defaults(func=cmd_delegate)
    dc = desub.add_parser("classify")
    dc.add_argument("task")
    dc.set_defaults(func=cmd_delegate)
    dp = desub.add_parser("plan")
    dp.add_argument("task")
    dp.set_defaults(func=cmd_delegate)

    pa = sub.add_parser("pa", help="Route /pa or /btw prompts through the personal-assistant router")
    pa.add_argument("--directive", action="store_true", help="Print hook-friendly routing instructions")
    pa.add_argument("prompt", nargs=argparse.REMAINDER)
    pa.set_defaults(func=cmd_pa)

    hk = sub.add_parser("hooks")
    hksub = hk.add_subparsers(dest="hooks_cmd", required=True)
    hksub.add_parser("doctor").set_defaults(func=cmd_hooks)

    pr = sub.add_parser("profile")
    prsub = pr.add_subparsers(dest="profile_cmd", required=True)
    prsub.add_parser("show").set_defaults(func=cmd_profile)
    ps = prsub.add_parser("set")
    ps.add_argument("name")
    ps.set_defaults(func=cmd_profile)

    be = sub.add_parser("bench")
    besub = be.add_subparsers(dest="bench_cmd", required=True)
    br = besub.add_parser("run")
    br.add_argument("--suite", default="framework-smoke")
    br.set_defaults(func=cmd_bench)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
