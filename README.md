# linkedleeds-demos

Demo websites for local businesses, served by GitHub Pages at **https://demos.linkedleeds.com/<slug>/**.

- `data/<slug>.json`: real facts about one business (from its Google listing). Never invent prices, staff, awards or testimonials.
- `tools/build_site.py data/<slug>.json`: renders `<slug>/index.html` (one self-contained page).
- Media comes from Mixkit (free commercial license, no attribution required):
  - video `https://assets.mixkit.co/videos/<ID>/<ID>-720.mp4`
  - still `https://assets.mixkit.co/videos/<ID>/<ID>-thumb-720-0.jpg`
- Themes: blush, espresso, plum, navy, forest, charcoal.

Pages are `noindex` because they are previews. When a business buys its site, move it to its own domain (or into Lovable) and remove it from this repo.
