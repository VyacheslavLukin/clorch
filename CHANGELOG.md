# Changelog

## [0.3.0] — 2026-03-02

### Added
- **Usage overview**: today's Claude Code cost, tokens, cache hit rate, and burn rate in header bar
  - Parses `~/.claude/projects/*/*.jsonl` session logs with incremental byte-offset tailing
  - Per-model pricing: Opus 4.6/4.5, Opus 4.1/4, Sonnet, Haiku 4.5, Haiku 3.5
  - Cost displayed as API equivalent (`~$28.61`) — useful for Max subscribers to see what they'd pay
  - In/Out token counts exclude cache reads to show real consumption
  - Cache hit rate, message count, burn rate ($/hr rolling 10-min window)
  - Per-agent token usage and cost in detail panel
- Midnight rollover: usage stats reset at local midnight
- Polling: JSONL files scanned every 10s (active sessions incremental, full scan every 60s)

## [0.2.0] — 2026-02-27

### Added
- **YOLO mode**: auto-approve all tool requests for tmux agents (`[!]` to toggle)
- **Rules engine**: configurable auto-approve/deny rules via `~/.config/clorch/rules.yaml`
  - Per-tool rules with optional regex pattern matching on tool summary
  - Deny rules force manual review even in YOLO mode
  - First matching rule wins, default: ask
- Live staleness indicators: yellow/red age timer on agents idle >30s/120s
- Git context: branch name and dirty file count in session list and agent detail
- Tools/min rate metric in header bar
- Auto-sync hook scripts on TUI startup (no manual `clorch init` after upgrades)
- Sound alerts on status changes: Sosumi (permission), Ping (answer), Basso (error)
- Smart `[y]` key: auto-approve single pending permission without selecting action
- Approve/deny actions logged to event panel
- Settings panel with sound toggle (`[s]` key)
- Blinking YOLO badge in header bar when active

## [0.1.0] — 2026-02-26

Initial release.
