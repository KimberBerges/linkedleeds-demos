#!/usr/bin/env python3
"""Build a one-page demo website for a local business from a JSON lead file.

Usage:
    python3 tools/build_site.py data/<slug>.json      # writes <slug>/index.html
    python3 tools/build_site.py data/*.json           # rebuild all

Media comes from Mixkit (free commercial license, no attribution required):
    video: https://assets.mixkit.co/videos/<ID>/<ID>-720.mp4
    still: https://assets.mixkit.co/videos/<ID>/<ID>-thumb-720-0.jpg
Use real facts only (from the Google listing). Never invent prices, staff,
awards or testimonials.
"""
import html
import json
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent

THEMES = {
    # name: (background, surface, ink, muted, accent, accent_ink, soft)
    "blush":    ("#fbf6f2", "#ffffff", "#3a1f24", "#7a6266", "#7b2d3b", "#fff7f3", "#f3dfd8"),
    "espresso": ("#f8f4ee", "#ffffff", "#2b211b", "#6f6259", "#2f241e", "#f8f4ee", "#e9dfd2"),
    "plum":     ("#f7f2ef", "#ffffff", "#2d1830", "#6d5a6f", "#4a1f4f", "#fbf4ea", "#eadde8"),
    "navy":     ("#f4f6f9", "#ffffff", "#14213d", "#56627a", "#14213d", "#ffffff", "#dde4ef"),
    "forest":   ("#f3f6f1", "#ffffff", "#1d2b22", "#5b6b60", "#2e5939", "#ffffff", "#dbe7dc"),
    "charcoal": ("#f5f5f3", "#ffffff", "#1c1c1c", "#5f5f5f", "#d4552b", "#ffffff", "#ecebe7"),
}
GOLD = "#b8924a"


def esc(s):
    return html.escape(str(s), quote=True)


def mix_video(i):
    return f"https://assets.mixkit.co/videos/{i}/{i}-720.mp4"


def mix_still(i):
    return f"https://assets.mixkit.co/videos/{i}/{i}-thumb-720-0.jpg"


def tel(phone):
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) == 10:
        digits = "1" + digits
    return "tel:+" + digits


def build(lead):
    t = THEMES.get(lead.get("theme", "espresso"), THEMES["espresso"])
    bg, surface, ink, muted, accent, accent_ink, soft = t
    name = lead["name"]
    city = lead["city"]
    state = lead.get("state", "FL")
    phone = lead["phone"]
    tel_link = tel(phone)
    address = lead["address"]
    maps_q = quote(f"{name}, {address}")
    directions = f"https://www.google.com/maps/dir/?api=1&destination={maps_q}"
    embed = f"https://www.google.com/maps?q={maps_q}&output=embed"
    cta_label = lead.get("cta_label", "Call Now")
    book = lead.get("booking_url")
    rating = lead.get("rating")
    reviews = lead.get("reviews")
    category = lead["category"]
    title = f"{name} | {category} in {city}, {state}"
    desc = lead.get("meta_description") or (
        f"{name} in {city}, {state}. " + ", ".join(s['name'] for s in lead["services"][:4])
        + (f". Rated {rating} on Google." if rating else "") + f" Call {phone}."
    )
    hero = lead["hero_video_id"]
    broll = lead.get("broll", [])          # [{id, caption}]
    gallery = lead.get("gallery_ids", [])  # list of Mixkit ids
    services = lead["services"]            # [{name, desc, image_id}]
    praise = lead.get("praise", [])        # [{title, text}]
    hours = lead.get("hours", [])          # [[day, text]]

    rating_badge = ""
    if rating and reviews:
        rating_badge = (
            f'<span class="badge"><span class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</span>'
            f'<b>{esc(rating)}</b> on Google <span class="dim">({esc(reviews)} reviews)</span></span>'
        )

    book_btn = (
        f'<a class="btn btn-primary" href="{esc(book)}" target="_blank" rel="noopener">Book Online</a>'
        if book else ""
    )

    def service_card(s):
        img = s.get("image_id")
        pic = (
            f'<img src="{mix_still(img)}" alt="{esc(s["name"])}" loading="lazy" width="1280" height="720">'
            if img else ""
        )
        return (
            f'<article class="card">{pic}<div class="card-body"><h3>{esc(s["name"])}</h3>'
            f'<p>{esc(s["desc"])}</p><a class="link" href="{tel_link}">Call for pricing &rarr;</a></div></article>'
        )

    broll_html = "".join(
        f'<figure class="clip"><video data-inview muted loop playsinline preload="none" '
        f'poster="{mix_still(b["id"])}" src="{mix_video(b["id"])}" aria-label="{esc(b["caption"])}"></video>'
        f'<figcaption>{esc(b["caption"])}</figcaption></figure>'
        for b in broll
    )
    gallery_html = "".join(
        f'<img src="{mix_still(g)}" alt="{esc(category)} inspiration" loading="lazy" width="1280" height="720">'
        for g in gallery
    )
    praise_html = "".join(
        f'<div class="praise"><h3>{esc(p["title"])}</h3><p>{esc(p["text"])}</p></div>' for p in praise
    )
    hours_html = "".join(
        f'<tr><td>{esc(d)}</td><td class="{"dim" if h.lower() == "closed" else ""}">{esc(h)}</td></tr>'
        for d, h in hours
    )

    schema = {
        "@context": "https://schema.org",
        "@type": lead.get("schema_type", "LocalBusiness"),
        "name": name,
        "telephone": phone,
        "address": {"@type": "PostalAddress", "streetAddress": address},
    }
    if rating and reviews:
        schema["aggregateRating"] = {"@type": "AggregateRating", "ratingValue": str(rating), "reviewCount": str(reviews)}

    headline = lead.get("headline", f"{category} in {city}")
    sub = lead.get("subheadline", "")
    intro = lead.get("intro")
    intro_html = (
        f'<section class="wrap intro"><p class="eyebrow">{esc(lead.get("intro_eyebrow", "About"))}</p>'
        f'<h2>{esc(lead.get("intro_title", "Welcome"))}</h2><p class="lead">{esc(intro)}</p></section>'
        if intro else ""
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="noindex">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{mix_still(hero)}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Jost:wght@300;400;500&display=swap" rel="stylesheet">
<link rel="preload" as="image" href="{mix_still(hero)}">
<script type="application/ld+json">{json.dumps(schema)}</script>
<style>
:root{{--bg:{bg};--surface:{surface};--ink:{ink};--muted:{muted};--accent:{accent};--accent-ink:{accent_ink};--soft:{soft};--gold:{GOLD}}}
*{{box-sizing:border-box;margin:0}}html{{scroll-behavior:smooth}}
body{{font-family:Jost,system-ui,sans-serif;background:var(--bg);color:var(--ink);line-height:1.6;font-weight:300}}
h1,h2,h3{{font-family:"Cormorant Garamond",Georgia,serif;font-weight:500;line-height:1.08}}
a{{color:inherit}}img,video{{display:block;max-width:100%}}
.wrap{{max-width:1120px;margin:0 auto;padding:0 20px}}
header{{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(10px);border-bottom:1px solid var(--soft)}}
header .wrap{{display:flex;align-items:center;justify-content:space-between;gap:12px;padding-top:12px;padding-bottom:12px}}
.logo{{font-family:"Cormorant Garamond",serif;font-size:1.5rem;font-weight:600;text-decoration:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.btn{{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:12px 22px;border-radius:999px;font-weight:500;text-decoration:none;transition:transform .2s,box-shadow .2s;white-space:nowrap}}
.btn:hover{{transform:translateY(-2px)}}
.btn-primary{{background:var(--accent);color:var(--accent-ink);box-shadow:0 12px 30px -14px var(--accent)}}
.btn-ghost{{border:1px solid color-mix(in srgb,var(--ink) 25%,transparent);background:color-mix(in srgb,var(--surface) 70%,transparent)}}
.hero{{position:relative;min-height:88vh;display:flex;align-items:center;overflow:hidden;color:#fff}}
.hero video,.hero .poster{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
.hero::after{{content:"";position:absolute;inset:0;background:linear-gradient(100deg,rgba(0,0,0,.66),rgba(0,0,0,.35) 55%,rgba(0,0,0,.15))}}
.hero .wrap{{position:relative;z-index:1;padding-top:90px;padding-bottom:90px}}
.hero h1{{font-size:clamp(2.6rem,7vw,5rem);max-width:13ch}}
.hero p.sub{{font-size:1.15rem;max-width:34ch;margin:18px 0 28px;opacity:.92}}
.hero .btn-ghost{{color:#fff;border-color:rgba(255,255,255,.5);background:rgba(255,255,255,.08)}}
.actions{{display:flex;flex-wrap:wrap;gap:12px}}
.badge{{display:inline-flex;align-items:center;gap:8px;padding:8px 16px;border-radius:999px;background:rgba(255,255,255,.14);backdrop-filter:blur(6px);font-size:.95rem;margin-bottom:22px}}
.stars{{color:var(--gold);letter-spacing:2px}}.dim{{opacity:.7}}
section{{padding:84px 0}}
.eyebrow{{text-transform:uppercase;letter-spacing:.28em;font-size:.75rem;color:var(--gold);font-weight:500}}
h2{{font-size:clamp(2rem,4.5vw,3.2rem);margin:10px 0 0}}
.lead{{font-size:1.15rem;max-width:62ch;margin-top:16px;color:var(--muted)}}
.grid{{display:grid;gap:22px;margin-top:44px}}
.cards{{grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}}
.card{{background:var(--surface);border:1px solid var(--soft);border-radius:22px;overflow:hidden;transition:transform .25s,box-shadow .25s}}
.card:hover{{transform:translateY(-4px);box-shadow:0 24px 50px -30px rgba(0,0,0,.35)}}
.card img{{aspect-ratio:4/3;object-fit:cover;width:100%}}
.card-body{{padding:22px}}.card h3{{font-size:1.6rem}}.card p{{color:var(--muted);margin:6px 0 14px}}
.link{{color:var(--accent);font-weight:500;text-decoration:none}}
.band{{background:var(--soft)}}
.clips{{grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}}
.clip{{border-radius:22px;overflow:hidden;background:var(--surface)}}
.clip video{{aspect-ratio:4/5;object-fit:cover;width:100%}}
.clip figcaption{{padding:16px 20px;font-family:"Cormorant Garamond",serif;font-size:1.4rem}}
.praises{{grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}}
.praise{{background:var(--surface);border-radius:22px;padding:26px;border-top:3px solid var(--gold)}}
.praise h3{{font-size:1.5rem}}.praise p{{color:var(--muted);margin-top:6px}}
.gallery{{grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}}
.gallery img{{aspect-ratio:1;object-fit:cover;border-radius:18px;width:100%}}
.note{{font-size:.85rem;color:var(--muted);margin-top:8px}}
.visit{{display:grid;gap:36px;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));align-items:stretch}}
table{{width:100%;border-collapse:collapse;margin-top:26px}}td{{padding:11px 0;border-bottom:1px solid var(--soft)}}td+td{{text-align:right}}
iframe{{width:100%;min-height:380px;height:100%;border:0;border-radius:22px}}
footer{{background:var(--accent);color:var(--accent-ink);padding:52px 0 28px}}
footer .cols{{display:grid;gap:24px;grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}}
footer .logo{{font-size:1.9rem}}footer p{{opacity:.85;font-size:.95rem}}
.copy{{text-align:center;opacity:.6;font-size:.8rem;margin-top:36px}}
.callbar{{display:none}}
@media (max-width:640px){{header .btn-ghost{{display:none}}.callbar{{display:flex;position:fixed;bottom:14px;left:14px;right:14px;z-index:30}}.callbar .btn{{flex:1}}body{{padding-bottom:70px}}}}
@media (prefers-reduced-motion:reduce){{.hero video,.clip video{{display:none}}.clip{{background-size:cover}}}}
.rise{{animation:rise .9s ease-out both}}@keyframes rise{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:none}}}}
</style>
</head>
<body>
<header><div class="wrap">
  <a class="logo" href="#top">{esc(name)}</a>
  <div class="actions"><a class="btn btn-ghost" href="{tel_link}">{esc(phone)}</a>{book_btn or f'<a class="btn btn-primary" href="{tel_link}">{esc(cta_label)}</a>'}</div>
</div></header>
<main id="top">
<section class="hero" style="padding:0">
  <img class="poster" src="{mix_still(hero)}" alt="" aria-hidden="true">
  <video autoplay muted loop playsinline preload="auto" poster="{mix_still(hero)}" src="{mix_video(hero)}" aria-hidden="true"></video>
  <div class="wrap rise">
    {rating_badge}
    <h1>{esc(headline)}</h1>
    <p class="sub">{esc(sub)}</p>
    <div class="actions">
      <a class="btn btn-primary" href="{tel_link}">{esc(cta_label)} &middot; {esc(phone)}</a>
      {book_btn}
      <a class="btn btn-ghost" href="{directions}" target="_blank" rel="noopener">Get Directions</a>
    </div>
  </div>
</section>
{intro_html}
<section class="wrap" id="services">
  <p class="eyebrow">Services</p><h2>{esc(lead.get("services_title", "What we do"))}</h2>
  <div class="grid cards">{"".join(service_card(s) for s in services)}</div>
</section>
{f'<section class="band"><div class="wrap"><p class="eyebrow">{esc(lead.get("broll_eyebrow", "In the details"))}</p><h2>{esc(lead.get("broll_title", "See the craft"))}</h2><div class="grid clips">{broll_html}</div></div></section>' if broll else ''}
{f'<section class="wrap"><p class="eyebrow">Why clients choose us</p><h2>What customers notice</h2><div style="margin-top:20px">{rating_badge.replace("rgba(255,255,255,.14)","var(--soft)")}</div><div class="grid praises">{praise_html}</div></section>' if praise else ''}
{f'<section class="wrap"><p class="eyebrow">Gallery</p><h2>Inspiration</h2><p class="note">Your own photos go here.</p><div class="grid gallery">{gallery_html}</div></section>' if gallery else ''}
<section class="wrap" id="visit">
  <div class="visit">
    <div>
      <p class="eyebrow">Visit</p><h2>Hours &amp; location</h2>
      <table>{hours_html}</table>
      <p class="lead" style="font-size:1rem">{esc(address)}</p>
      <div class="actions" style="margin-top:18px"><a class="btn btn-primary" href="{tel_link}">{esc(cta_label)}</a><a class="btn btn-ghost" href="{directions}" target="_blank" rel="noopener">Get Directions</a></div>
    </div>
    <iframe title="Map to {esc(name)}" src="{embed}" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
  </div>
</section>
</main>
<footer><div class="wrap">
  <div class="cols">
    <div><div class="logo">{esc(name)}</div><p>{esc(category)} in {esc(city)}, {esc(state)}</p></div>
    <div><p>{esc(address)}</p><p><a href="{tel_link}">{esc(phone)}</a></p></div>
    <div>{"".join(f"<p>{esc(d)}: {esc(h)}</p>" for d, h in hours)}</div>
  </div>
  <p class="copy">&copy; {esc(name)}</p>
</div></footer>
<div class="callbar"><a class="btn btn-primary" href="{tel_link}">{esc(cta_label)} &middot; {esc(phone)}</a></div>
<script>
(function(){{
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var vids = document.querySelectorAll('video[data-inview]');
  if (!('IntersectionObserver' in window)) {{ vids.forEach(function(v){{v.play().catch(function(){{}})}}); return; }}
  var io = new IntersectionObserver(function(es){{ es.forEach(function(e){{ if (e.isIntersecting) e.target.play().catch(function(){{}}); else e.target.pause(); }}); }}, {{threshold:.3}});
  vids.forEach(function(v){{ io.observe(v); }});
}})();
</script>
</body>
</html>
"""


def main(paths):
    for p in paths:
        lead = json.loads(Path(p).read_text())
        out = ROOT / lead["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build(lead))
        print(f"built {out.relative_to(ROOT)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
