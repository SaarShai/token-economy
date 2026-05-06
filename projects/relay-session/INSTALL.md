# relay-session install

## Install From GitHub

From the target repo:

```bash
curl -fsSL https://raw.githubusercontent.com/SaarShai/token-economy/main/projects/relay-session/install.sh \
  | bash -s -- --target "$PWD" --copy --install-skill
python3 -m relay_session.cli --help
```

This copies the standalone Python package into the repo and installs the
`relay-sessions` Codex skill into `${CODEX_HOME:-$HOME/.codex}/skills`.

## Copy-only install from checkout

```bash
cp -R projects/relay-session/relay_session /path/to/target-repo/
cd /path/to/target-repo
python3 -m relay_session.cli --help
```

## Symlink install

```bash
bash projects/relay-session/install.sh --target /path/to/target-repo
```

The installer creates `/path/to/target-repo/relay_session` as a symlink to this
package. Use `--copy` if you want a physical copy.

Install the Codex skill too:

```bash
bash projects/relay-session/install.sh --target /path/to/target-repo --copy --install-skill
```

## Relay Launch

```bash
python3 -m relay_session.cli relay \
  --repo "$PWD" \
  --name "my-task" \
  --version 01 \
  --execute
```

The successor receives only `start.md` when present plus the generated handoff.
It does not inherit the old transcript unless it later calls `ask-old` with an
explicit question.

If the old session identifies an even older relay handoff as the source, the
successor should repeat `ask-old` with that older handoff and the same narrow
question.

Use `ask-old` without `--execute` to dry-run routing. Add `--execute` to
actually ask the old session. Narrow repo retrieval means targeted reads/searches
of known files, status, or symbols; it does not mean loading broad archives.
