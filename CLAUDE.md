# Watching Christmas: build instructions for Claude

You are continuing **Watching Christmas**, an interactive WebGL globe of the Christmas films each country watches or makes. A previous session built and tested a complete **United Kingdom** version. Your job is to **finish it for every country that has data**, without changing the design or behaviour already agreed.

The owner is Matt; call him Matt. State your understanding before you start, ask before assuming anything not written here, and give a token-cost estimate before heavy work.

## 1. Repository map

| Path | What it is |
|---|---|
| `site/index.html` | The whole app (HTML, CSS and JS in one file). It runs as a Claude artifact or as any static site. |
| `site/data/countries.json` | Natural Earth 1:50m borders. Per-country properties: `n` name, `iso`, `lx`/`ly` label point, `st` status for US-movies mode, `lo` status for Country-specific mode. Status values: `has` (has films) or `none` (no data). |
| `site/data/markets.json` | Film data keyed by ISO2 for every country with data (98 entries), plus `GLOBAL` (Global Top 10) and the marker territories `GP`, `MQ`, `RE`. |
| `site/posters/*.jpg` | Poster images (JustWatch `s332` size). |
| `scripts/fetch_justwatch_offers.py` | Fetches the JustWatch US page for each film and pulls the JSON-LD direct links and `countryOfOrigin`. |
| `scripts/build_markets.py` | Builds `markets.json` for every country and sets the `st`/`lo` statuses in `countries.json`. Also writes `scripts/posters_manifest.json`. |
| `scripts/fetch_posters.py` | Downloads the posters listed in `posters_manifest.json` (JustWatch `s332` first). |
| `scripts/find_justwatch_slugs.py` | Finds JustWatch pages for guide-2 films with no working JustWatch link, accepting a page only when its year matches. Results: `scripts/justwatch_slug_matches.json`. |
| `.github/workflows/pages.yml` | Publishes `site/` to GitHub Pages on every push to `main` (https://dattmalley.github.io/WatchingChristmas/). Needs Settings → Pages → Source: "GitHub Actions" turned on once. |
| `scripts/prep_countries.py` | Builds `countries.json` from Natural Earth. |
| `scripts/justwatch_offers.json` | Cached JustWatch offers, origin and poster for every unique film (135 pages). Re-runs only fetch what's missing. |
| `source/Holiday-Films-US-Ratings.csv` | **Guide 1**: what each country watches most. 942 rows, 96 `audience_market` values, US ratings, US watch options. |
| `source/Holiday-Films-by-Country-of-Origin.csv` | **Guide 2**: films made in each country. 138 rows, 42 `country` sections, local ratings, subscription, free, rental and purchase services. |
| `source/Holiday-Films-All-Country-Entries-With-Trailers.csv` | Matt's all-entries file (26 Nov 2026): one row per country entry (1,095), each with `trailer_url`. **The build's trailer source.** Trailers are identical for a film across countries. Its 5 `poster_index_only` films (A Christmas Carol 2009, Candy Cane Lane, Love the Coopers, Miracle on 34th Street 1947, Scrooged) belong to no country list; by Matt's decision they join the Country specific list of the country JustWatch says made them (all US, positions 11–15). |
| `source/Holiday-Film-Trailers.csv` | Earlier per-film trailer list; superseded by the all-entries file and kept for reference. |
| `source/*.docx` | The two guides as documents, including their methods and limits. Read the rating and ranking caveats. |
| `source/archive/…_2026-11-24_no-ratings.docx` | Earlier 24 Nov edition of guide 1, without US ratings. Replaced by `source/Christmas-Holiday-Film-Watch-Guide-US.docx`; kept for reference only. |

There is no separate "global" file. Each guide ends with a **Global Top Ten** section, and guide 1's CSV includes it as `audience_market = "Global Top Ten"`.

**Live preview (a private Claude artifact):** https://claude.ai/artifact/YDyQ8vY9pPVCXk4G5BkaUZ. To update it from a Claude session, read it first (`Artifact` `action: "read"`) and then publish to that `url`; don't create a new artifact. The repository is the source of truth, so keep the two in sync.

## 2. What is built (keep all of it)

- **Stage:**
  - A WebGL 2 globe (globe.gl 2.46.2 via jsDelivr, which bundles three.js) with **no atmosphere** and **`autoRotateSpeed = 0.02`**.
  - Natural Earth 1:50m borders.
  - Snow (canvas), string lights (SVG) and a night-maroon background.
  - The globe pauses rendering while a panel is open.
  - GSAP 3.15.0 and ScrollTrigger via jsDelivr, with `gsap.ticker.lagSmoothing(0)`.
- **Title pill (top-left):** "Watching Christmas" in **Cherry Swash Bold**, red, **no white outline**, **no tree**, plus a chip showing the current mode. Clicking it reopens the welcome card. **Nothing at the top right**; the location display was removed on purpose.
- **Globe hover (Matt, 26 Nov 2026):** a country with films turns **Christmas green `#00873E`** (`--xmas-green`, `COL.hasHover`); no-data countries keep their subtle dark hover.
- **No-data countries (Matt, 26 Nov 2026):** muted red-and-white **candy-cane stripes** (diagonal in latitude + longitude, fixed to the land), so they read as disabled; slightly brighter on hover. Done by borrowing globe.gl's cap `MeshBasicMaterial` class and patching its shader (`caneMaterials()` in `index.html`). The map key's "No data" swatch uses the matching `--cane` gradient.
- **Favicon:** an inline SVG Christmas tree (green tree, gold star, red/gold/white baubles on maroon) in the `<link rel="icon">` data URI. The "no tree" rule above applies to the title pill only.
- **Map key:** a **"?" button** at the bottom right. Hover or focus shows the key, a click pins it, and it's hidden otherwise. Its wording follows the mode.
- **Welcome card:** shows on **every visit** (Matt, 26 Nov 2026; it used to show on the first visit only). It contains:
  - the title in Cherry Swash red with a drop shadow and no outline;
  - the line "Spin the globe and tap a country to see the Christmas films it watches most, ranked, rated and linked straight to the stream.";
  - the toggle **Global Top 10 | Country specific** (Global Top 10 first and default) with one line of help;
  - three CTAs: **"🎄 Open <detected country>"** (flies there and opens its panel, or the Santa card if it has no data in the current mode), **"Global Top 10"** (opens the world list) and **"Explore the globe"** (closes the card).
  The country is guessed from the time zone, then the browser language, falling back to the United Kingdom. The artifact host blocks the geolocation API, so there's no permission prompt. (This replaced the earlier "Open United Kingdom" and "Spin to my country" buttons; see section 4.)
- **Toggle meaning (decided by Matt, don't change it):**
  - **Global Top 10** (Matt, 26 Nov 2026; replaced "US movies" as the first option, data key still `us`): the clicked country's **complete** guide-1 most-watched Top 10, **every film wherever it was made** (the US-made filter was removed). Numbers are that country's ranks. The filter uses US ratings: All, G, PG, PG-13, R, TV, Unverified. Each row shows the index score and its origin line. The world list (`GLOBAL`) opens from the bottom-left button and the welcome card's "Global Top 10" button.
  - **Country specific:** the clicked country's guide-2 list of films made there, filtered by **that country's own rating** (UK: BBFC U, PG, 12A, 15, 18, Unverified), with the US rating shown beside it as a dashed chip. It's numbered in research order and labelled as not a viewing ranking. Never convert ratings between countries.
  - Film origin comes from guide 2's `country_of_origin` by title match. If a film isn't in guide 2, fall back to JustWatch's `countryOfOrigin` and flag it in the row as "(origin per JustWatch)". JustWatch gives only one country and is sometimes wrong, so prefer the documents.
  - The mode is remembered in localStorage (`cw-mode`), and the globe recolours per mode.
- **Country panel (holly-red card):**
  - The header has the country name and a mode-specific subtitle on the left. The white close button is at the **far top right**, with the **toggle directly under it**. On phones, the toggle takes its own row under the close button.
  - There is **no eyebrow line and no circular badge**; both were removed on purpose.
  - Rating tabs show counts, and a tab with zero films is disabled.
  - Each film row reads, in order: poster with a rank bubble, title (Saira Condensed) with rating chip(s), year and origin line, runtime as "1h 37m" plus minutes, and a single **"Where to watch"** column.
  - **GSAP `ScrollTrigger.batch`** staggers rows in, and a **ScrollTrigger snap** settles the list on row edges. The open animation flies the globe to the country first, with the view snapped to 5°.
- **Watch-button rules (decided by Matt):**
  - **Maximum 3 buttons per film**, filled in priority order **Stream, then Free, then Rent/Buy**.
  - **No prices.**
  - Buttons are full width and stay inside the column (long names shorten with "…").
  - Links go **straight to the film** on the service, taken from the JustWatch US page's JSON-LD `potentialAction` WatchAction `urlTemplate`, matched by provider name. A service with no direct link gets an outlined button that opens the JustWatch page.
  - A film with no offers shows one dashed **"Unavailable"** button.
  - Links are **US only** for now (`LINK_REGION = "US"`). The data shape `watch: { US: {stream, free, rentbuy} }` allows other regions later. Matt would eventually like links to follow the visitor's country.
  - Provider names are normalised (see `brand()` in `build_markets.py`): Netflix Standard with Ads becomes Netflix, Peacock Premium becomes Peacock, Disney Plus becomes Disney+, Amazon Video becomes Amazon, channel variants merge into their brand.
- **Footer** text depends on the mode (check dates; the index is not a viewer count; the research selection is not a ranking).
- **Design references** (Dribbble, which may need allowing in network settings):
  - [9145599](https://dribbble.com/shots/9145599-Merry-Christmas): sage green, brush script, white cards.
  - [17138133](https://dribbble.com/shots/17138133-Christmas-Gift-App-UI-Design): dark maroon, red circular buttons, condensed titles.
  - [26653081](https://dribbble.com/shots/26653081-Merry-Christmas): holly red, string lights, glass panels, white pill buttons.
  - [27920691](https://dribbble.com/shots/27920691-Christmas-Shopping-App-UI-UX-Design-Mobile-App-Concept): not yet reviewed.
  - The title font matches the "A Christmas Story" (1983) logo lettering, without its white outline.

## 3. The job: finish every country with data

1. **Data:**
   - Generalise `scripts/build_markets.py` to build `markets.json` entries for **every** guide-1 market (US movies mode) and **every** guide-2 country (Country specific mode), keyed by ISO2. Use the existing schema:
     `{ISO2: {name, code, lat, lng, us: {sources, films: [...]}, local: {authority, scale: [...], films: [...]}}}`.
   - A country may have only one mode.
   - Derive `local.authority` and `local.scale` per country from guide 2's `rating_authority` and `country_rating`.
2. **Links:** fetch the JustWatch US page once per **unique** film (about 1 second between requests) and apply the watch rules. Commit the offers cache under `scripts/` so later runs don't need to fetch again.
3. **Posters:** download the `s332` JustWatch poster for each unique film into `site/posters/`. Artifact pages can't load images from other sites. To mirror the site to the artifact: at most 255 files and 64 MB per publish, so publish in batches to the same URL.
4. **Globe status:** every country with data in the current mode is clickable and opens its panel. Replace the old "live / ready for full build" statuses with **"has films"** and **"no data"**.
5. **New requirement:** if a country has **no data in the current mode**, clicking it opens a small card with a **Santa Claus illustration** saying **"No data for this country"**.
   - Draw an original Santa as inline SVG. Don't copy a film's or brand's character.
   - Animate it in with GSAP and match the existing card style.
   - Update the map key, and update the welcome card's CTAs if needed.
6. **Verify:**
   - Test in the pre-installed Playwright Chromium (use the flags `--ignore-gpu-blocklist --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`; WebGL is slow there, so allow long waits) at 1440×900 and 390×844.
   - Check: no console errors, no sideways scrolling, every country opens, at most 3 buttons per film, and no button outside its column.
7. **Ship:** commit to a feature branch, push, mirror the result to the live artifact, and report what changed.

## 4. Ask Matt before building

- Guide 1 has extra rows: "Global Top Ten", "China unranked example", Hong Kong, Taiwan, Guadeloupe, Martinique, Réunion and New Caledonia. The last four have no shape of their own on the Natural Earth 1:50m map, and guide 2 has a separate "Soviet Union" section. How should each be shown? (Ideas: a global top ten button, map markers for the territories, Soviet Union under Russia.)
- Many guide-1 films (for example Netflix originals) aren't in guide 2, so US-made filtering will often depend on JustWatch's single-country origin. Is that acceptable?
- Should "Open United Kingdom" on the welcome card stay, or change (for example to the visitor's detected country)?

### Answers (Matt, 26 Nov 2026), now built
- "Global Top Ten": its own panel (`GLOBAL`), opened from the **Global Top 10** button at the bottom left and on the welcome card. Global Top 10 mode only.
- "China unranked example": dropped (its two films are Chinese-made and already in guide 2 under China).
- Guadeloupe, Martinique, Réunion: clickable **map markers**. Hong Kong, Taiwan and New Caledonia use their own shapes.
- "Soviet Union": merged into **Russia**'s Country specific list, each film labelled "(Soviet-era film)".
- Origin: guide 2 by normalised title + year (or watch URL), else JustWatch `countryOfOrigin`, flagged. Films with neither show "Origin not recorded" (they were left out while the US-made filter existed).
- Welcome card: shows on every visit, with **"Open <detected country>"** (time zone, then browser language; falls back to the UK) and **"Explore the globe"**. "Spin to my country" was removed.
- No data in the current mode (clicking a shape or marker, or toggling inside a panel): the **Santa card** opens, with a button to the other mode when that has films.

## Build commands
```
python3 -I scripts/fetch_justwatch_offers.py scripts/justwatch_offers.json --from-csv source/Holiday-Films-US-Ratings.csv source/Holiday-Films-by-Country-of-Origin.csv
python3 -I scripts/find_justwatch_slugs.py source/Holiday-Films-by-Country-of-Origin.csv scripts/justwatch_offers.json scripts/justwatch_slug_matches.json
python3 -I scripts/build_markets.py scripts/justwatch_offers.json site source/Holiday-Films-US-Ratings.csv source/Holiday-Films-by-Country-of-Origin.csv source/Holiday-Films-All-Country-Entries-With-Trailers.csv
python3 -I scripts/fetch_posters.py scripts/posters_manifest.json site/posters
python3 -I scripts/build_markets.py scripts/justwatch_offers.json site source/Holiday-Films-US-Ratings.csv source/Holiday-Films-by-Country-of-Origin.csv source/Holiday-Films-All-Country-Entries-With-Trailers.csv
```
Playwright in the cloud container must launch Chromium with `proxy: { server: process.env.HTTPS_PROXY, bypass: 'localhost,127.0.0.1' }`, or the CDN scripts never load. A WebGL screenshot takes about 20 s there.

## 5. Environment notes

- Reachable last time: cdn.jsdelivr.net, unpkg.com, cdnjs.cloudflare.com, raw.githubusercontent.com, www.justwatch.com, images.justwatch.com and registry.npmjs.org.
- Blocked: dribbble.com (behind an AWS WAF challenge), github.com web pages, geoBoundaries, the UN geoportal and OpenDataSoft.
- NATO publishes no boundary data. For UN-based borders, UN Clear Map and geoBoundaries CGAZ need their hosts allowed first.
- Run Python on downloaded data with `python3 -I`.
- Recommended model: Opus. Fetching and building should be deterministic scripts, not model calls. Rough cost: 400–700k tokens.
