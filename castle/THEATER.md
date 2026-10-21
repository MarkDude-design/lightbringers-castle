# A small, scripted theater

`theater.html` is the Castle's first browser stage. It reads the ten existing
room scripts and the characters present in each room. Nothing in this page
invokes `talk.py`, `project_tasks.py`, model endpoints, or local tools.

## The first slice

- Choose one of ten doors; a room hash such as `#garden` opens that room.
- Give a character a cue to cycle through their stored responses.
- Nudge the scenery to cycle through the room's environment gags.
- Reveal the current joke, then reset or move to the next telling.
- Let Q add a stored cosmic aside. The host note explains the scripted personas.

The illustrated stage and palette are shared scenery. Room-specific
`interactions` descriptions remain story prompts, not executable actions or a
promise that every drawn object has a hot spot. This page does not save a
performance or add free-text chat.

## Preview

From the repository root, developers can serve only the public Castle directory:

```sh
python -m http.server 8765 --bind 127.0.0.1 --directory castle
```

Windows can use `py -3` in place of `python`. Open
`http://127.0.0.1:8765/theater.html`. This is a local preview, not deployment.
Opening this source HTML directly as a file cannot fetch its separate scripts;
use the static server or the self-contained review snapshot.

The host handoff also supplies a standalone `castle-theater-preview.html`:
download and open it directly, including on Windows. That review artifact
bundles a frozen copy of the public room/character scripts and styles. Its
hash-based content policy disables all connections; no server, account, key,
or dependency installation is needed. The normal site continues to read the
canonical JSON files; no duplicate room/character data is committed here.
The snapshot builder and browser-check script are included in the handoff.
The managed test browser blocks `file://` navigation by administrator policy.
The byte-identical standalone artifact was checked over loopback as one HTML
document with no additional asset requests. Direct file-opening on Windows has
not been verified here; no browser policy was bypassed.

## Boundaries and failure behavior

The JavaScript has an explicit room/character ID list. Only those relative
same-origin JSON assets are fetched, with credentials omitted, redirects refused,
and an eight-second timeout. Adding a new script to the browser requires an
explicit list update. Source text is inserted with `textContent`; it is never
evaluated as code or inserted as HTML. The page's content policy permits only
its own scripts/styles/connections and denies inline code and form actions.

Successful assets are cached for this page. Failed fetches are not retried
automatically; a visitor can explicitly try again. A missing room has a visible
error and leaves the other doors usable. A missing character leaves the rest
of the cast usable. A delayed room response cannot replace a newer room choice.
No local storage, telemetry, external fonts, remote assets, or model calls are
part of the stage. These are browser-page controls, not a new OS sandbox or
permission to attach APIs, credentials, or MCP later.

## Verification

`python scripts/verify.py` discovers the new script as a fifth JavaScript syntax
check and runs all existing offline suites/static checks. No new dependencies
or browser installation are added to CI.

The implementation handoff records separate local Chromium/Playwright checks
for all rooms/cast/cues/jokes, keyboard/modal behavior, 320/390-pixel layouts,
missing assets/timeouts, delayed navigation, HTML-like text, unlisted IDs, content policy,
and the fully offline standalone snapshot. Those browser checks use the already
installed tools with a sanitized browser environment and blocked external
requests. CI syntax/unit checks are not claimed as browser UI coverage.

Mark owns merge. Scripted play does not accept any model artifact, alter task
accounting, or continue a closed live batch.
