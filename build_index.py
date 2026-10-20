"""Build index.html, a static visitor page for a saved exhibit.

    python3 build_index.py "Your Name" [app/exhibits/the-long-road-of-blue.json]

The page needs no server, so it works on GitHub Pages or opened straight from disk.
"""
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
curator = sys.argv[1] if len(sys.argv) > 1 else ""
src = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "app/exhibits/the-long-road-of-blue.json")
ex = json.load(open(src))
works = sorted(ex["works"], key=lambda w: w.get("sortYear", w.get("datebegin") or 0))
e = html.escape


def fmt(y):
    return f"{-y} BCE" if y < 0 else ("1 CE" if y == 0 else str(y))


# Scale strip, same math as the app.
years = [w.get("sortYear", w.get("datebegin") or 0) for w in works]
lo, hi = min(years), max(years)
span = max(hi - lo, 50)
step = next((s for s in (10, 25, 50, 100, 250, 500, 1000) if span / s <= 6), 1000)
lo, hi = lo - span * 0.04, hi + span * 0.04
x = lambda y: 30 + (y - lo) / (hi - lo) * 840
ticks, t = [], -(-int(lo) // step) * step
while t <= hi:
    ticks.append(f'<line class="tick" x1="{x(t):.1f}" y1="42" x2="{x(t):.1f}" y2="54"/><text class="tick-l" x="{x(t):.1f}" y="72" text-anchor="middle">{fmt(t)}</text>')
    t += step
dots, last, row = [], -99, 0
for i, y in enumerate(years):
    cx = x(y)
    row = (row + 1) % 2 if cx - last < 18 else 0
    last = cx
    dots.append(f'<circle class="dot" cx="{cx:.1f}" cy="48" r="6"/><text class="dot-l" x="{cx:.1f}" y="{18 if row else 32}" text-anchor="middle">{i + 1}</text>')


def stop(i, w):
    who = ", ".join([p for p in (w.get("artist"), w.get("culture"), w.get("period")) if p][:2])
    img = "app/static/" + w["localImage"] if w.get("localImage") else w.get("image", "")
    credit = (w.get("creditline") or "").split(", ", 1)[-1] if (w.get("creditline") or "").startswith("Harvard Art Museums/") else w.get("creditline") or ""
    dims = (w.get("dimensions") or "").splitlines()[0] if w.get("dimensions") else ""
    return f"""
    <li class="stop">
      <div class="node" aria-hidden="true"></div>
      <div class="stop-body">
        <div class="when"><b>{e(w.get("dated") or fmt(years[i]))}</b>{i + 1} of {len(works)}{" · " + e(w["classification"]) if w.get("classification") else ""}</div>
        <div class="pair">
          <figure><img src="{e(img)}" alt="{e(w["title"])}" loading="lazy"></figure>
          <article class="label">
            <h3>{e(w.get("displayTitle") or w["title"])}</h3>
            <div class="tomb">{f'<span class="who">{e(who)}</span>' if who else ""}<span>{e(w.get("dated") or "")}</span><span>{e(w.get("medium") or "")}</span>{f"<span>{e(dims)}</span>" if dims else ""}</div>
            <p>{e(w.get("body") or "")}</p>
            <div class="why"><span>Why it's here</span><p>{e(w.get("why") or "")}</p></div>
            <div class="credit"><span>{e(credit)}</span><a href="{e(w.get("url") or "")}">{e(w.get("objectnumber") or "")}</a></div>
          </article>
        </div>
      </div>
    </li>"""


page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(ex["title"])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Public+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root {{
  --wall: #f3f5f9; --label: #ffffff; --ink: #141a2e; --muted: #5a6380; --rule: #d7dce8; --accent: #1f3fa8;
  --display: "Cormorant Garamond", "Iowan Old Style", Georgia, serif;
  --body: "Public Sans", -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root {{ --wall: #0c1122; --label: #151c33; --ink: #e7ebf6; --muted: #9aa4c4; --rule: #2a3355; --accent: #93a9ff; color-scheme: dark; }}
}}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; }}
body {{ background: var(--wall); color: var(--ink); font: 400 1rem/1.6 var(--body);
       padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }}
.wrap {{ max-width: 1080px; margin: 0 auto; padding-block: 56px 72px; display: grid; gap: 48px; }}
a {{ color: var(--accent); text-underline-offset: 3px; }}
header {{ display: grid; gap: 16px; max-width: 46rem; }}
.eyebrow {{ font: 500 .76rem/1 var(--mono); letter-spacing: .14em; text-transform: uppercase; color: var(--accent); }}
h1 {{ font: 500 clamp(2.6rem, 7vw, 4.6rem)/1 var(--display); margin: 0; text-wrap: balance; }}
.curator {{ font: 500 .95rem/1.4 var(--body); color: var(--muted); margin: 0; }}
.curator b {{ color: var(--ink); font-weight: 600; }}
.intro {{ font-size: 1.1rem; margin: 0; max-width: 42rem; }}
.scale {{ display: grid; gap: 8px; }}
.scale-box {{ overflow-x: auto; }}
.scale svg {{ display: block; width: 100%; min-width: 560px; height: auto; }}
.axis {{ stroke: var(--rule); stroke-width: 2; }} .tick {{ stroke: var(--rule); }}
.tick-l {{ fill: var(--muted); font: 400 11px var(--mono); }} .dot {{ fill: var(--accent); }}
.dot-l {{ fill: var(--ink); font: 500 11px var(--mono); }}
ol.timeline {{ list-style: none; margin: 0; padding: 0; position: relative; }}
ol.timeline::before {{ content: ""; position: absolute; left: 7px; top: 8px; bottom: 8px; width: 2px; background: var(--rule); }}
.stop {{ display: grid; grid-template-columns: 16px minmax(0, 1fr); column-gap: 24px; padding-bottom: 56px; }}
.stop:last-child {{ padding-bottom: 0; }}
.node {{ width: 16px; height: 16px; border-radius: 50%; background: var(--accent); border: 4px solid var(--wall); margin-top: 6px; position: relative; z-index: 1; }}
.stop-body {{ display: grid; gap: 16px; min-width: 0; }}
.when {{ font: 500 .85rem/1.3 var(--mono); color: var(--accent); }}
.when b {{ font: 500 1.8rem/1.05 var(--display); color: var(--ink); display: block; margin-bottom: 4px; }}
.pair {{ display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr); gap: 28px; align-items: start; }}
figure {{ margin: 0; background: var(--label); border: 1px solid var(--rule); }}
figure img {{ display: block; width: 100%; height: auto; }}
.label {{ background: var(--label); border: 1px solid var(--rule); padding: 22px 24px 24px; display: grid; gap: 14px; min-width: 0; }}
.label h3 {{ font: 600 1.5rem/1.15 var(--display); margin: 0; text-wrap: balance; }}
.tomb {{ font-size: .86rem; line-height: 1.5; color: var(--muted); display: grid; gap: 2px; }}
.tomb .who {{ color: var(--ink); font-weight: 500; }}
.label p {{ margin: 0; font-size: .97rem; max-width: 65ch; }}
.why {{ border-top: 1px solid var(--rule); padding-top: 12px; display: grid; gap: 6px; }}
.why > span {{ font: 500 .7rem/1 var(--mono); letter-spacing: .14em; text-transform: uppercase; color: var(--accent); }}
.credit {{ font: 400 .74rem/1.5 var(--mono); color: var(--muted); display: flex; flex-wrap: wrap; gap: 4px 14px; justify-content: space-between; }}
footer {{ border-top: 1px solid var(--rule); padding-top: 18px; font-size: .84rem; color: var(--muted); }}
@media (max-width: 760px) {{
  .wrap {{ padding-block: 32px 48px; gap: 36px; }}
  .pair {{ grid-template-columns: minmax(0, 1fr); gap: 14px; }}
  .stop {{ column-gap: 14px; padding-bottom: 44px; }}
  .label {{ padding: 18px; }}
}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="eyebrow">An exhibition from the Harvard Art Museums collection</div>
    <h1>{e(ex["title"])}</h1>
    {f'<p class="curator">Curated by <b>{e(curator)}</b></p>' if curator else ""}
    <p class="intro">{e(ex.get("intro") or "")}</p>
  </header>
  <section class="scale" aria-label="Dates of the works on one scale">
    <div class="eyebrow" style="color:var(--muted)">Where the works fall, to scale</div>
    <div class="scale-box"><svg viewBox="0 0 900 86" role="img" aria-label="Dates of the works on one scale"><line class="axis" x1="30" y1="48" x2="870" y2="48"/>{"".join(ticks)}{"".join(dots)}</svg></div>
  </section>
  <ol class="timeline">{"".join(stop(i, w) for i, w in enumerate(works))}
  </ol>
  <footer>Object data from the Harvard Art Museums collection API. Images © President and Fellows of Harvard College. Each accession number links to the object's page on harvardartmuseums.org.</footer>
</div>
</body>
</html>
"""
with open(os.path.join(ROOT, "index.html"), "w") as f:
    f.write(page)
print("Wrote index.html" + (f" (curated by {curator})" if curator else " (no curator name)"))
