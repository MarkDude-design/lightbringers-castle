#!/usr/bin/env python3
"""Build a single-file offline Castle review from the canonical scripted theater."""
import argparse
import base64
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASTLE = ROOT / "castle"

def replace_one(s, old, new, label):
    if s.count(old) != 1:
        raise ValueError(label + ": anchor count " + str(s.count(old)))
    return s.replace(old, new, 1)

def build(out):
    html = (CASTLE / "theater.html").read_text(encoding="utf-8")
    css = (CASTLE / "theater.css").read_text(encoding="utf-8")
    js = (CASTLE / "scripts/theater.js").read_text(encoding="utf-8")
    icon = (CASTLE / "theater-icon.svg").read_bytes()
    rooms = re.search(r"const rooms = \[(.*?)\];", js, re.S)
    bots = re.search(r"const botIds = new Set\(\[(.*?)\]\);", js, re.S)
    if not rooms or not bots:
        raise ValueError("Canonical theater allowlist missing")
    room_ids = re.findall(r"\{id: '([^']+)'", rooms.group(1))
    bot_ids = set(re.findall(r"'([^']+)'", bots.group(1)))
    if "peanut_gallery" not in room_ids or len(room_ids) != len(set(room_ids)):
        raise ValueError("Eleventh door missing or duplicate IDs")
    scripts = {}
    cast_ids = {"q_overlay"}
    for rid in room_ids:
        room = json.loads((CASTLE / "rooms" / (rid + ".json")).read_text(encoding="utf-8"))
        if room["id"] != rid:
            raise ValueError("Room ID mismatch: " + rid)
        scripts["rooms/" + rid + ".json"] = room
        cast_ids.update(room.get("bots_present", []))
    for bid in sorted(cast_ids & bot_ids):
        file = CASTLE / "bots" / (bid + ".json")
        if file.is_file():
            bot = json.loads(file.read_text(encoding="utf-8"))
            if bot["id"] != bid:
                raise ValueError("Bot ID mismatch: " + bid)
            scripts["bots/" + bid + ".json"] = bot
    payload = json.dumps(scripts, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    shim = (
        "const __reviewScripts = " + payload + ";\n"
        "const fetch = async (p) => ({\n"
        "  ok: Object.prototype.hasOwnProperty.call(__reviewScripts,p),\n"
        "  json: async () => __reviewScripts[p]\n"
        "});\n"
    )
    js = re.sub(
        r"history\.replaceState\([^;]+;",
        "try { history.replaceState(null, '', '#' + id); } catch { /* restricted file URL */ }",
        js, count=1
    )
    notes_js = """
const reviewNote = document.getElementById('voice-review-notes');
const reviewStatus = document.getElementById('review-note-status');
const reviewText = () => 'Castle offline review / ' + new Date().toISOString() +
  '\\nCurrent room: ' + (location.hash || '#courtyard') +
  '\\n\\nDictated feedback:\\n' + reviewNote.value + '\\n';
document.getElementById('review-copy').addEventListener('click', async () => {
  if (!reviewNote.value.trim()) { reviewStatus.textContent='Dictate a note first.'; return; }
  try {
    if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(reviewText());
    else { reviewNote.focus();reviewNote.select();
      if (!document.execCommand('copy')) throw Error('blocked'); }
    reviewStatus.textContent='Copied. Paste into the chat.';
  } catch { reviewStatus.textContent='Copy blocked. Use Save notes or select and copy.'; }
});
document.getElementById('review-save').addEventListener('click', () => {
  if (!reviewNote.value.trim()) { reviewStatus.textContent='Dictate a note first.'; return; }
  const blob = new Blob([reviewText()], {type:'text/plain;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href=url;
  a.download='castle-dictated-feedback.txt';
  document.body.append(a);a.click();a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10000);
  reviewStatus.textContent='Saved locally; nothing uploaded.';
});
"""
    inlined_js = shim + js + notes_js
    if "</script" in inlined_js.lower():
        raise ValueError("Unsafe script terminator in inline content")
    csp = ("default-src 'none'; script-src 'unsafe-inline'; "
           "style-src 'unsafe-inline'; img-src data:; connect-src 'none'; "
           "base-uri 'none'; object-src 'none'; form-action 'none'")
    html = re.sub(
        r'(<meta http-equiv="Content-Security-Policy" content=")[^"]+(">)',
        lambda m:m.group(1)+csp+m.group(2), html, count=1
    )
    html = replace_one(html, '<link rel="stylesheet" href="theater.css">',
        "<style>\n" + css + "\n</style>", "stylesheet")
    html = replace_one(html,
        '<script type="module" src="scripts/theater.js"></script>',
        '<script type="module">\n' + inlined_js + '\n</script>', "script")
    icon64 = base64.b64encode(icon).decode("ascii")
    html = replace_one(html,
        '<link rel="icon" type="image/svg+xml" href="theater-icon.svg">',
        '<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,'+icon64+'">', "icon")
    html = replace_one(html, 'href="theater.html"', 'href="#courtyard"', "home")
    html = replace_one(html, 'Ten strange rooms, a scripted cast',
                       'Eleven strange rooms, a scripted cast', "count meta")
    html = replace_one(html, 'Ten rooms.<br>Absolutely no sensible ones.',
                       'Eleven rooms.<br>Absolutely no sensible ones.', "count menu")
    review = """
      <section class="voice-review" aria-labelledby="voice-review-title">
        <p class="eyebrow">OPTIONAL · PRIVATE REVIEW</p>
        <h2 id="voice-review-title">Speak your notes as you browse.</h2>
        <p>Use the keyboard microphone on your phone. Mention the room and what
        made you smile, what confused you, or what you would change. This page
        never uploads your notes. Copy or save before closing.</p>
        <label for="voice-review-notes">Your feedback</label>
        <textarea id="voice-review-notes" rows="5" placeholder="Peanut Gallery: ...&#10;What made me smile: ..."></textarea>
        <div class="voice-review-actions">
          <button id="review-copy" type="button">Copy feedback</button>
          <button id="review-save" type="button">Save notes as text</button>
          <span id="review-note-status" role="status" aria-live="polite"></span>
        </div>
      </section>
"""
    style = """
.voice-review {margin:30px 0 64px;padding:25px;border:1px solid var(--line);
border-radius:12px;background:#fffcf6;}
.voice-review h2 {font-family:var(--serif);font-size:clamp(25px,3vw,36px);font-weight:normal;margin:0 0 8px;}
.voice-review p {max-width:760px;color:var(--muted);}
.voice-review label {display:block;font-size:13px;font-weight:bold;margin:15px 0 8px;}
.voice-review textarea {display:block;width:100%;min-height:135px;padding:14px;font:inherit;
color:var(--ink);background:white;border:1px solid #a6b7ab;border-radius:8px;resize:vertical;}
.voice-review-actions {display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:12px;}
.voice-review-actions button {padding:12px 16px;border:1px solid var(--ink);
border-radius:7px;background:var(--ink);color:white;}
#review-note-status {font-size:12px;color:var(--muted);}
"""
    html = replace_one(html, "</style>", style + "\n</style>", "notes CSS")
    html = replace_one(html, "    </main>", review + "    </main>", "notes panel")
    html = replace_one(html, "Some ideas are fragments. They’re welcome here, too.",
        "Some ideas are fragments. They’re welcome here, too. This offline copy uses scripted lines only; no live models or checkpoint receipts.", "host note")
    for forbidden in ['src="scripts/theater.js"', 'href="theater.css"', 'href="theater-icon.svg"']:
        if forbidden in html:
            raise ValueError("Unbundled dependency: " + forbidden)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return {"rooms":len(room_ids),"bundled_scripts":len(scripts),
            "bytes":out.stat().st_size,"output":str(out)}

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=ROOT / "dist/castle-review-offline.html")
    args=parser.parse_args()
    print(json.dumps(build(args.output), sort_keys=True))
