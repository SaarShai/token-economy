# relay-session install

## Copy-only install

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

