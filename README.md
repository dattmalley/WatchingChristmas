# WatchingChristmas

**Christmas Watchlist** is an interactive WebGL globe of the Christmas films each country watches most, or makes itself. Each film is rated and linked straight to where it streams.

The United Kingdom is complete in this version. The plan for finishing every other country is in [`CLAUDE.md`](CLAUDE.md).

## Run it

Serve the `site/` folder with any static server:

```bash
cd site && python3 -m http.server 8765
```

Then open http://localhost:8765. The page loads globe.gl, GSAP and Google Fonts from public CDNs.

## Features

- A 3D globe with real country borders (Natural Earth 1:50m) that turns slowly. Click a country to see its films.
- **US movies / Country specific** toggle:
  - **US movies:** the country's most-watched Christmas films that were made in the US, filtered by US rating.
  - **Country specific:** films made in that country, filtered by its own rating board (for the UK, the BBFC), with the US rating beside it.
- Each film shows a poster, title, runtime, and up to three "Where to watch" links, in the order Stream, then Free, then Rent/Buy. Each link opens the film directly on the service. Links are US only for now.
- Animated with GSAP: rows stagger in as you scroll, and the list snaps to rows.

## Data

The source guides and CSVs are in `source/`. The scripts in `scripts/` turn them into `site/data/*.json` and fetch the direct streaming links and posters from JustWatch.

The rankings are research estimates, not viewer counts. See the guides for their methods and limits.
