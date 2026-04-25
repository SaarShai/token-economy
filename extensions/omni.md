# Omni Extension

Claude-specific pre/post hook output filter. Token Economy does not vendor Omni.

## Adopted Natively

- Raw-output archive and `rewind`: `./te output-filter rewind`.
- Savings stats: `./te output-filter stats`.
- Custom rules: `./te output-filter rules --init`, then edit `.token-economy/output-filter-rules.txt`.
- Session-aware suppression: `./te output-filter filter --session-aware` or `output_filter_session_aware: true`.

## Still External

Use Omni itself only when its host-specific hook integration is better than `hooks/output-filter/filter.sh`.
