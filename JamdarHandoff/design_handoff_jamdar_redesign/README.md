# Handoff: Jamdar — Desktop UI Redesign

## Overview
Jamdar is a desktop music-finder/downloader. This package redesigns its main interface
from a cramped dark utility into a bright, soft, premium surface. The product lets a user
**search** YouTube + SoundCloud (and bulk-import a Spotify playlist), **preview** 30-second
clips inline, **download** tracks as MP3/FLAC to a chosen output drive, and watch progress
in a slide-out **download queue**. A persistent dark **Now Playing** dock anchors the bottom.

The redesign's core ideas:
- Warm "paper" surfaces, generously rounded cards, two soft shadow tiers.
- A **single coral accent** (`#FF82A8`) does the heavy lifting; ink-on-coral CTAs.
- A **dark indigo-ink dock** for the player so the coral pops and the player feels premium.
- **Platform colors** (YouTube red, SoundCloud orange, Spotify green) appear ONLY as small
  accent moments — a thumbnail badge, a source-label dot — never as fills or clutter.

## About the Design Files
The files in this bundle are **design references created in HTML/CSS** — a static hi-fi
mockup showing the intended look and behavior. They are **not production code to ship
directly**. There is no application logic, routing, audio playback, or networking here;
the waveform bars are decorative and built by a tiny inline script.

Your task is to **recreate these designs in the target codebase's existing environment**
(React, Vue, SwiftUI, Electron, Tauri, native, etc.) using its established components,
state patterns, and libraries. If no environment exists yet, choose the most appropriate
framework for a cross-platform desktop app (this mockup is desktop-window-shaped — Electron
or Tauri + a web framework is a natural fit) and implement there. Use the HTML/CSS as the
**visual spec**: match the tokens, spacing, type, and states precisely, but wire up real
behavior in idiomatic code.

## Fidelity
**High-fidelity (hifi).** Colors, typography, spacing, radii, shadows, and component states
are all final and intentional. Recreate the UI pixel-faithfully using the codebase's
patterns. Exact token values are in **Design Tokens** below and in `assets/jamdar.css`.

---

## Layout & Dimensions

The mockup window is drawn at **1280 wide** (the inner app shell) inside a presentation page.
The app shell is a single window with four stacked regions:

```
┌─────────────────────────────────────────────────────────────┐
│ TITLEBAR            height 52px                               │
├─────────────────────────────────────────────────────────────┤
│ SEARCH HEADER       padding 22/24px, border-bottom           │
├──────────────────────────────────┬──────────────────────────┤
│ RESULTS (flex:1)                 │ QUEUE PANEL  width 330px   │  body: flex, height 512px
│ scrollable card feed             │ slide-out, dockable        │
├──────────────────────────────────┴──────────────────────────┤
│ NOW PLAYING DOCK    height 96px, dark                        │
└─────────────────────────────────────────────────────────────┘
```

- **Window shell**: `border-radius: 32px`, `overflow: hidden`, large pop shadow, paper background.
- **Body**: `display:flex; height:512px`. Results column is `flex:1`; queue is a fixed
  `330px` right column with a `1px` left hairline. The queue is a **dockable slide-out** —
  when collapsed it disappears and its active count shows as a badge on the titlebar download icon.
- Responsive: at `≤980px` the foundations/notes grids collapse to a single column (presentation
  page only — the app window itself is designed for desktop width).

---

## Screens / Views

There is **one primary screen** (the main window) plus documented **component variations**.

### Screen: Main Window
**Purpose:** search for a track, preview it, and download it; monitor the download queue.

#### Region 1 — Titlebar (height 52px)
Translucent white (`rgba(255,255,255,.65)`, `backdrop-filter: blur(8px)`), bottom hairline.
Left → right, gap 16px, horizontal padding 18px:
1. **Traffic lights** — three 12px dots (`#FF5F57`, `#FEBC2E`, `#28C840`), gap 8px. (macOS-style; map to the host OS chrome in a real app.)
2. **Brand** — 24px "disc" mark (radial gradient: white center → coral ring → ink outer) + wordmark "Jamdar" in display font, 800, 18px.
3. **Spacer** (flex:1).
4. **Output-drive chip** (`.uchip.drive`) — pill, white, hairline border, 34px tall. Green status dot + drive icon + mono path text `SANSA CLIP /Music` (truncates with ellipsis, max 200px).
5. **Format segmented control** (`.seg`) — pill containing `MP3` (active) / `FLAC`. Active segment = white fill + small shadow.
6. **Downloads icon button** (`.iconbtn`) — 36px pill, with a coral **count badge** (`2`) top-right (mono, ink-on-coral).
7. **Settings icon button** — 36px pill, gear glyph.

#### Region 2 — Search Header
Padding `22px 24px 20px`, subtle top white gradient, bottom hairline.
- **Search bar** (`.searchbar`) — full-width white pill, hairline border, card shadow, padding `8px 8px 8px 18px`. Contains: magnifier glyph (ink-3) · text input (16px, ink, current value `"bonobo - kerala"`) · **source segmented control** `[All sources | ● YouTube | ● SoundCloud]` (dots are platform-colored 8px) · **coral Search button** (`.btn-primary`, 44px pill, display font 700, coral glow shadow).
- **Sub-row** (margin-top 14px): **Spotify import field** (`.import`, flex:1 pill) with a green Spotify badge, placeholder `"Paste a Spotify playlist link to bulk-download…"`, and a soft-green **Import playlist** button (`.btn-spotify`, green-soft bg `#DEF6E6`, text `#0c7a39`). To its right, a **hint**: `⏎ to search · 30s previews` (kbd chip for the ⏎).

#### Region 3a — Results Feed (left, flex:1)
Padding `18px 20px 8px`, column flex.
- **Results head**: `Results` (display 700, 17px) · mono count `24 tracks` · spacer · **sort pill** `Relevance` (white pill, list-glyph).
- **Card list** (`.cardlist`): vertical stack, gap 12px, of **result cards**.

**Result card (`.rcard`)** — the workhorse component. White, `border-radius: 20px`, hairline border, card shadow, padding 14px, `display:flex; align-items:center; gap:16px`:
- **Cover** — `80×80`, `border-radius:15px`, inset hairline. Filled with an abstract gradient placeholder (real app: album/thumbnail art). Has a **grain overlay** and a **platform badge** (`.pbadge`) bottom-left: 20px tall, mono 10px, white text on a semi-opaque platform color (`YT` on `rgba(255,59,48,.92)`, `SC` on `rgba(255,85,0,.92)`), with a 6px white dot.
- **Meta** (flex:1, min-width:0): **title** (display 700, ~16.5px, truncates) + **sub-line** (gap 9px): a colored **source label** (`SoundCloud`/`YouTube` with a matching platform dot, 12.5px 600) · 3px separator dot · uploader · mono **duration** (`6:18`).
- **Actions** (flex, gap 9px): **Preview** ghost button (`.btn-ghost`, white pill, hairline, play glyph) · **Download** coral button (`.btn-dl`, coral pill, ink text, download glyph) · **open-in-browser** icon button (`.linkbtn`, 34px, external-link glyph).
- **Playing state (`.rcard.playing`)**: border goes transparent and gains a **2px coral ring** (`box-shadow: 0 0 0 2px coral`); the cover gets a **3px coral ring + coral glow**; the sub-line shows a live **equalizer** (`.eq`, 4 animated coral bars) with the text `Now previewing`; the Preview button becomes a **Pause** button outlined in coral with coral-deep text.

#### Region 3b — Download Queue (right, 330px)
White, left hairline, column flex. Dockable slide-out.
- **Queue head**: `Downloads` (700, 16px) · coral **`2 active`** badge (mono) · spacer · **dock/collapse** chevron button (`.mini`, 30px).
- **Queue list** (`.qlist`): stack, gap 10px, of **queue rows**.

**Queue row (`.qrow`)** — `surface-2` bg, hairline, `border-radius:15px`, padding `11px 12px`:
- **Top**: 38px cover (`border-radius:9px`) · meta (title 600 13px, truncates; **format chip** `.fmt` in mono — `MP3 · 320` / `FLAC`) · **cancel ✕** circular button (`.qcancel`, 26px).
- **Active state**: **coral progress bar** (`.bar`, 7px pill track, fill is a `coral → coral-deep` gradient) + a **status row** with `Downloading…` and a **mono percentage** (`64%`). Progress bar + % must **always be visible while active** (hard requirement).
- **Done state (`.qrow.done`)**: green-soft bg `#DEF6E6`, green border; status `✓ Saved to drive` (green `#1a8c47`) + file size (`9.1 MB`); the trailing button becomes **reveal-in-drive** (folder glyph).
- **Fail state (`.qrow.fail`)**: red-soft bg `#FDECEE`, red border; status `⚠ Source unavailable` (red `#d23b4e`) + a **Retry** text button (coral-deep, refresh glyph).

#### Region 4 — Now Playing Dock (height 96px, dark)
`linear-gradient(180deg, #2C2541, #211B30)`, light ink, top dock-line. `display:flex; align-items:center; gap:20px; padding:0 22px`. Left → right:
1. **Meta** (`.npmeta`, width 286px): 60px cover (`border-radius:13px`, ring + drop shadow) · title (display 700, 15px, light) + sub-line (`● Bonobo · YouTube` with platform dot) + a coral **`PREVIEW`** tag (mono, coral on translucent-coral).
2. **Transport** (`.transport`): restart (`.tbtn`, 38px, muted) · **coral Play/Pause** (`.play`, 52px circle, coral, ink glyph, coral glow) · stop (`.tbtn`).
3. **Scrubber** (`.scrub`, flex:1): current time (mono, white, right-aligned, 42px) · **waveform** (`.wave`, 34px tall, 3px bars at `rgba(255,255,255,.16)`, played bars in coral, with a white **playhead** dot ringed in translucent coral) · total time (mono, muted). For a 30s preview, default played ≈ 37%.
4. **Right** (`.right`): **volume** (icon + 5px track, white-ish fill at 62%) · **Download** button (`.dock-dl`, translucent-white pill, white text) — one-tap save of the track you're previewing.

---

## Component Variations (to choose from)

The mockup presents alternates; **the main window uses Card A + Player A.** Pick one of each.

### Result card
- **Card A — Standard row** (used in main window): the `.rcard` described above. Horizontal art + meta + explicit Preview/Download buttons. Best for scannability and density.
- **Card B — Cover-forward**: larger 104px cover with a centered play affordance on hover, a faint platform-tinted left gradient wash, source label above the title, and an **inline mini-waveform + mono duration + Download** row (no separate Preview button — clicking the cover previews). More media-rich, slightly lower density.

### Now Playing player
- **Player A — Dark dock** (used in main window): the dark `.dock` above. Premium, high-contrast, lets coral pop.
- **Player B — Light glass dock**: same layout on a light glassy surface (`linear-gradient(#fff,#FBF4F6)`) with an **art-bloom background** (coral + indigo radial glows), a hairline border, ink text, a coral-soft `PREVIEW` tag, and a **solid coral** Download button with coral glow. Lighter, airier; lower contrast against the paper body.

---

## Interactions & Behavior

Implement these in real code (the mockup only shows static states):

- **Search**: typing a query + Enter (or the Search button) runs a search across the selected
  source(s). Source segmented control filters `All / YouTube / SoundCloud`. Show `N tracks` count.
- **Spotify import**: pasting a Spotify playlist URL + Import enqueues every track for matching/
  download (bulk). (Spotify is used for the track list; audio is fetched from YT/SC.)
- **Preview**: clicking Preview/▶ on a card (or the cover in Card B) starts a **30s preview**;
  that card enters the `playing` state (coral ring + equalizer) and the **dock** populates with
  its meta, transport, scrubber, and `PREVIEW` tag. Only one card previews at a time. Play
  toggles to Pause. Stop clears the dock state.
- **Scrubber**: clicking/dragging the waveform seeks within the preview; playhead + played-bars
  + current-time update. Volume control adjusts output level.
- **Download**: Download (card, dock, or Card B inline) enqueues the track using the **titlebar
  format** (MP3·320 / FLAC) into the configured **output drive**. A new queue row appears in the
  active state.
- **Queue**: each active row shows a live **coral progress bar + %**. ✕ cancels. On success →
  `done` state (green, file size, reveal-in-drive). On failure → `fail` state (red, Retry which
  re-enqueues). The titlebar download **badge** reflects the active count. The chevron
  **docks/collapses** the panel to the window edge.
- **Output drive chip / format / settings** open their respective controls (drive picker,
  format toggle, settings).

### Animations
- **Equalizer** (`@keyframes eq`): 4 bars scale Y between 0.4 and 1.0, `1s ease-in-out infinite`,
  staggered delays (`-.2s / -.5s / 0s / -.35s`). Only on the previewing card.
- **Card hover**: `.rcard` transitions `transform` and `box-shadow` over `.15s ease` (add a
  subtle lift on hover in implementation).
- **Waveform** in the mockup is decorative/deterministic; in production drive it from real
  playback position.

### States to implement
- Result card: default, hover, **playing**.
- Queue row: **active (downloading)**, **done (saved)**, **fail (unavailable)**.
- Buttons: default / hover / active / focus (add focus-visible rings for accessibility).
- Empty results, loading/searching, and no-network are not drawn — design them consistently
  with the system (paper surface, coral accent, mono helper text).

## State Management
State the implementation will need:
- `query`, `sourceFilter` (`all | youtube | soundcloud`), `searchResults[]`, `resultCount`,
  `sort` (`relevance | …`).
- `format` (`mp3 | flac`), `outputDrivePath`.
- `nowPlaying` (track id, isPlaying, positionSec, durationSec=30, volume) — drives both the
  dock and the card `playing` state.
- `downloadQueue[]` — each item: `{ id, title, art, source, format, status: 'downloading'|'done'|'fail', progress, sizeBytes? }`.
- `queueOpen` (docked vs collapsed) + derived `activeCount` for the badge.
- Data fetching: search APIs per source, Spotify playlist resolution, and the actual
  audio-stream + download pipeline (out of scope for the visual spec, but the UI assumes
  streamed previews and progress events).

---

## Design Tokens

All tokens live as CSS custom properties in `assets/jamdar.css` (`:root`). Port them to the
target system's token format (CSS vars, a theme object, Tailwind config, etc.).

### Colors
**Surfaces / ink**
| Token | Hex | Use |
|---|---|---|
| `--bg` | `#EDE6E0` | page behind the window |
| `--paper` | `#FAF6F2` | app window canvas |
| `--surface` | `#FFFFFF` | cards |
| `--surface-2` | `#F5EFEA` | insets / utility chips / queue rows |
| `--surface-3` | `#EFE7E1` | progress tracks |
| `--ink` | `#221C2B` | primary text (warm indigo-black) |
| `--ink-2` | `#6E6577` | secondary text |
| `--ink-3` | `#A79FAC` | tertiary / placeholder |
| `--line` | `#ECE3DC` | hairline |
| `--line-2` | `#E0D5CC` | stronger hairline / borders |

**Brand (coral accent)**
| Token | Hex | Use |
|---|---|---|
| `--coral` | `#FF82A8` | primary accent, CTAs (ink text on coral) |
| `--coral-deep` | `#E85684` | small coral text / links / retry |
| `--coral-soft` | `#FFE6EE` | tints, token boxes |
| `--coral-tint` | `#FFF2F6` | faintest tint |

**Dock (dark anchor)**
| Token | Hex |
|---|---|
| `--dock` | `#211B30` |
| `--dock-2` | `#2C2541` |
| `--dock-3` | `#3A3253` |
| `--dock-line` | `rgba(255,255,255,.10)` |
| `--dock-ink` | `#EBE6F2` |
| `--dock-ink-2` | `#A49CB8` |

**Platform (accent only — never large fills)**
| Token | Hex |
|---|---|
| `--yt` / `--yt-soft` | `#FF3B30` / `#FFE5E3` |
| `--sc` / `--sc-soft` | `#FF5500` / `#FFE9DC` |
| `--spotify` / `--spotify-soft` | `#1DB954` / `#DEF6E6` |

**Semantic status:** saved/done green text `#1a8c47` (bg `#DEF6E6`, border `#cdeed8`);
fail red text `#d23b4e` (bg `#FDECEE`, border `#F6D2D7`).

### Typography
Google Fonts: **Bricolage Grotesque** (display), **Hanken Grotesk** (body/UI), **JetBrains Mono** (mono).
```
--font-display: "Bricolage Grotesque", system-ui, sans-serif;  /* weights 500/600/700/800 */
--font-body:    "Hanken Grotesk", system-ui, sans-serif;        /* weights 400/500/600/700 */
--font-mono:    "JetBrains Mono", ui-monospace, monospace;      /* weights 400–700 */
```
- Headings use display font, `letter-spacing: -.02em`.
- Mono is used for **time codes, percentages, format chips, drive paths, counts/badges**, and uses tabular numerals (`font-feature-settings:"tnum" 1`).
- Scale (from the mockup): display/hero 30–54px/800; card title ~16.5px/700; section title 30px/700; body & buttons 13–15px/600; sub-lines 12.5–13.5px; mono details 10–12.5px.

### Spacing & Radii
4-pt rhythm. Radii: `--r-xs:8` · `--r-sm:11` (chips, tags) · `--r:15` (inputs, queue rows, covers) · `--r-lg:20` (result cards, panels) · `--r-xl:26` · `--r-2xl:32` (window shell) · `--pill:999` (buttons, badges, segmented controls).

### Shadows
```
--sh-1:    0 1px 2px rgba(34,28,43,.05), 0 1px 3px rgba(34,28,43,.04);
--sh-2:    0 2px 8px rgba(34,28,43,.05), 0 12px 30px rgba(34,28,43,.08);
--sh-card: 0 1px 0 rgba(34,28,43,.03), 0 10px 26px rgba(34,28,43,.06);
--sh-pop:  0 18px 50px rgba(34,28,43,.16);          /* window shell */
--glow-coral: 0 8px 24px rgba(255,130,168,.45);     /* coral CTAs / play button */
```

### Page background
Two soft radial glows over the base, used behind the window (presentation context):
```
radial-gradient(1200px 600px at 15% -8%, #FBEFF1, transparent 60%),
radial-gradient(1000px 560px at 100% 0%, #EEF0FF, transparent 55%),
#EDE6E0
```

---

## Assets
- **No real image assets** are used. Album/thumbnail art is faked with **gradient placeholders**
  (`.a1`–`.a7` in the CSS) plus a striped **grain** overlay. In production, replace these with
  real cover/thumbnail images from the search results; keep the inset hairline + rounded corners.
- **Icons** are inline SVG strokes (search, download, settings/gear, external-link, play/pause/
  stop, volume, chevron, folder, retry, etc.). Use the codebase's existing icon set (e.g. Lucide/
  Feather-style 1.7–2.2 stroke) to match; sizes run ~13–22px.
- **Fonts** load from Google Fonts (see Typography). Self-host or use the app's font pipeline as appropriate.
- `screenshots/` in the source project contains reference renders (window, dock, player B) if you
  want pixel references — ask the designer to include them; they are not bundled here by default.

## Files in this bundle
- `Jamdar Redesign.html` — the full hi-fi mockup: main window, component notes, variations, and a
  foundations section (palette, type, spacing, ASCII wireframe). Open in a browser to inspect every state.
- `assets/jamdar.css` — the complete design system: tokens + every component's styles. This is the
  source of truth for exact values.

> Note: the inline `<script>` at the bottom of the HTML only builds decorative waveform bars — it is
> not application logic. Ignore it when porting behavior.
