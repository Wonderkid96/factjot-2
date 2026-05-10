# v1 Reference

The v1 codebase that v2 references is at:

`/Users/Music/Developer/Insta-bot/`

**Never** `/Users/Music/Documents/Insta-bot/` — iCloud sync in `Documents/` intercepts FFmpeg writes and produces silent 14-min encode hangs (per v1 `CLAUDE.md` §6).

v1 is **read-only**. v2 reads v1 to understand decisions; v2 never imports, symlinks to, or modifies v1.

When in doubt about path, run:
```bash
ls /Users/Music/Developer/Insta-bot/CLAUDE.md
```
This file must exist. If it doesn't, the path is wrong.
