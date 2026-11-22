# Sunday 22 November 2026 — The World in One Day

[![make.fun](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/competitions/news-image-20261122)
[![make.fun rank](https://make.fun/badge/news-image-20261122/rank.svg)](https://make.fun/competitions/news-image-20261122)
[![make.fun reward](https://make.fun/badge/news-image-20261122/reward.svg)](https://make.fun/competitions/news-image-20261122)

A one-page newspaper front page summing up Sunday 22 November 2026 in a single
image — 35 stories, 3 leads, 13 pictures, 20 briefs, 7 regions, a UTC timeline,
and a date check. Built for the [make.fun](https://make.fun) bounty
**news-image-20261122** ("Sum up 22 November's world news in one image").

## What changed vs v3

v3 ranked 490/7,458 (judge 0.980122) but the top-50 line had risen to 0.987920.
The live top 10 all share the same story skeleton as v3 — the gap is craft:

- **Typography:** a hand-typed slab-serif stroke display font now carries the
  masthead, hero headlines and section headers (v3 used the blocky 5x7 pixel
  font everywhere, which read as a poster, not a newspaper). The 5x7 stays for
  card headlines, decks, briefs and footers.
- **Illustration richness:** hero scenes now have sky gradients, a conference
  table with delegates and a gavel (COP31), radar dishes with flames (Bahrain),
  searchlight cones, drones and a lit skyline (Kyiv); card art fills its box.
- **Two verified missing stories added:** Wembanyama's 50-point first in NBA
  history (50 pts, 19 reb, 5 blocks, 4 steals — verified Reuters/AP) and the
  Belgian air-traffic controllers' strike (429 flights / ~59,500 passengers —
  verified Belga/AFP/Xinhua). Both appear as picture cards in the rank-1 entry.
- **Date discipline:** the DATE CHECK footer now reads "WIRES READ UP TO
  14:00 UTC" (v3 said 08:00 UTC while its own timeline already ran to 14:00).

## How to run

```sh
python3 main.py          # writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png)
```

Self-contained, Python 3 stdlib only (`os`, `struct`, `zlib`) — a pure-Python PNG
encoder, hand-typed bitmap fonts and vector drawing. No network, no PIL, no
file reads. Two runs produce byte-identical output.

## Contents

- `main.py` — the whole generator (1024x1024 front page)
- 3 illustrated leads (COP31 final text / Iran-Bahrain claim / 186 drones),
  12 picture cards, 20 ALSO briefs, a 6-number strip, a UTC timeline, a
  14-pin world map, and a DATE CHECK footer naming what was left out on
  purpose and what is not yet known.
