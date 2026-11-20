# 🖱️ botyaraclick

> **From Garage to Galaxy** — a full-featured idle/clicker game built with Python + Pygame.

Start as a freelancer in a garage, click your way to building an IT empire, and eventually launch rockets into space. 176 upgrades, 30 random events, 13 themes, and a prestige system that keeps pulling you back.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.0%2B-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ Features

### 🎮 Core Gameplay
- 🖱️ **Click to earn** — write code, earn dollars, build the empire
- 💰 **176+ upgrades** across 6 categories and 23 branches
- 👥 **Hire staff** for passive income — interns → AI engineers
- 🏢 **7 progression eras** — Garage → Home Office → Startup → IT Company → Corporation → Megacorp → Space Age
- ⭐ **Prestige system** — reset for permanent Reputation Point bonuses
- 🎲 **30 random events** — golden objects, market booms, crises, challenges, investor deals

### 🎨 Visual Polish
- ✨ **Particle effects** — sparks, coins, confetti, stars
- 💥 **Click animations** — spring bounce, screen shake, floating numbers
- 🎨 **13 hand-crafted themes** — Cyberpunk, Cozy Forest, Retro 8-bit, Royal Gold, Deep Space, Deep Ocean, Infernal, Halloween, Winter Wonderland, and more
- 🔤 **Offline fonts + emoji** — every theme font (plus Noto Emoji) ships in `assets/fonts`; Cyrillic and emoji fall back automatically, no more ▯ boxes
- 🔔 **Calm toasts** — short notifications in the bottom corner, 1 click to dismiss, hover to pause the timer
- 🌧️ **Animated background effects** per theme — matrix rain, falling leaves, snowflakes, embers, bubbles, bats, stars, scanlines
- 🏆 **50 achievements** with small bonuses (including **6 secret ones**)

### 💾 Quality of Life
- 💾 **5 save slots** with auto-save every 30 seconds
- 🌐 **Localization** — English & Russian included; template provided for easy adding
- ⚙️ **Full settings menu** — audio, visuals, number formats, effects toggle
- 🔊 **Sound system** — separate SFX and music volume controls
- 📊 **Detailed stats** — total clicks, per-era playtime, achievements progress
- 🖥️ **Fullscreen & windowed** mode — `F11` to toggle
- ⌨️ **`Space` to click** — keyboard-friendly

---

## 🚀 Quick Start

```bash
git clone https://github.com/dimasbotyara/botyaraclick.git
cd botyaraclick

python -m venv .venv
source .venv/bin/activate     # Linux / macOS
# .venv\Scripts\activate      # Windows

pip install -r requirements.txt
python main.py
```

**One-click launchers** are also included: `run.sh`, `run.bat`, `run.ps1`.

**Everything is bundled** — fonts, sounds, music all ship with the project. No extra downloads.

---

## 🎯 Upgrade Categories

| Category | Branches | Type | Count |
|----------|----------|------|-------|
| 🖥️ Equipment | Computer, Workplace, Peripherals, Internet | Click power | 32 |
| 👥 Staff | Developers, Management, Marketing, Support | Passive income | 32 |
| 🏗️ Infrastructure | Offices, Servers, Energy, Transport | Multipliers | 32 |
| 📱 Products | Software, Platforms, Hardware, R&D | Passive income | 32 |
| 🎯 Skills | Clicker, Business, Charisma, Luck | Permanent bonuses | 24 |
| 🏛️ Empire | Real Estate, Media, Space | Endgame | 24 |
| **Total** | **23 branches** | | **176** |

---

## 🎨 Themes

Each theme comes with its own font, palette, and animated background effect:

| # | Theme | Font | Background |
|---|-------|------|------------|
| 1 | Business *(default)* | Montserrat | — |
| 2 | Cyberpunk / Neon | Orbitron | Matrix Rain |
| 3 | Cozy Forest | Comfortaa | Falling Leaves |
| 4 | Retro 8-bit | Pixelify Sans | Scanlines |
| 5 | Royal Gold | Cinzel | Gold Sparkle |
| 6 | Deep Space | Exo 2 | Stars |
| 7 | Candy Land | Sniglet | Bubbles |
| 8 | Hacker / Terminal | Fira Code | Matrix Rain |
| 9 | Minimalism | Montserrat | — |
| 10 | Deep Ocean | Bubblegum Sans | Bubbles |
| 11 | Infernal | Rubik Glitch | Embers |
| 12 | Halloween | Creepster | Bats |
| 13 | Winter Wonderland | Caveat | Snowflakes |

---

## ⭐ Prestige System

Once you've earned **$500M total**, you can **Prestige**:

- All money and upgrades reset
- You earn **Reputation Points (RP)**
- RP formula: `floor(√(total_earned / 500,000,000))`
- Spend RP on **permanent bonuses** that persist through every future run
- Achievements, prestige upgrades, and statistics are **preserved**

The loop is the point — every reset makes the next run faster, deeper, and more absurd.

---

## ⌨️ Hotkeys

| Key | Action |
|-----|--------|
| `Space` | Click |
| `Escape` | Pause / Back |
| `F5` | Quick Save |
| `F11` | Toggle Fullscreen |
| `Shift + Close` | Quit with save/no-save choice |

---

## 📂 Project Structure

```
botyaraclick/
├── main.py                     # Entry point
├── game.py                     # Main game class (state machine)
├── config.py                   # Global constants & settings
├── economy.py                  # Economic calculations & number formatting
│
├── core/                       # Core systems
│   ├── save_manager.py         # Save/load (5 slots + global)
│   ├── sound_manager.py        # Sound & music manager
│   ├── event_system.py         # Random events
│   └── achievement_tracker.py  # Achievement tracking
│
├── data/                       # Game data
│   ├── upgrades.py             # 176 upgrades
│   ├── achievements.py         # 50 achievements
│   ├── events.py               # 30 random events
│   ├── eras.py                 # 7 progression eras
│   ├── themes.py               # 13 visual themes
│   └── prestige.py             # Prestige system
│
├── screens/                    # Game screens
│   ├── language_select.py      # First-run language picker
│   ├── main_menu.py            # Main menu
│   ├── save_load.py            # 5-slot save selector
│   ├── settings.py             # Settings
│   ├── game_screen.py          # Main gameplay
│   ├── pause_menu.py           # Pause menu
│   ├── upgrade_tree.py         # Upgrade tree view
│   ├── themes_shop.py          # Theme shop
│   └── prestige_screen.py      # Prestige
│
├── ui/                         # Reusable UI components
│   ├── fonts.py                # Offline fonts + Cyrillic/emoji fallback
│   ├── button.py               # Buttons
│   ├── panel.py                # Panels & overlays
│   ├── scrollbar.py            # Scroll areas
│   ├── slider.py               # Sliders
│   ├── tooltip.py              # Tooltips
│   ├── notification.py         # Toasts
│   └── popup.py                # Popup dialogs
│
├── effects/                    # Visual effects
│   ├── particles.py            # Particle system
│   ├── floating_text.py        # Floating numbers
│   ├── animations.py           # Animations
│   └── bg_effects.py           # Animated backgrounds
│
├── locales/                    # Localization
│   ├── locale_manager.py       # Locale manager (auto-detects)
│   ├── lang_en.py              # English
│   ├── lang_ru.py              # Russian
│   └── lang_template.py        # Copy me to add a language
│
├── assets/                     # Bundled fonts, sounds, music
│   ├── fonts/                  # TTF fonts (OFL)
│   ├── sounds/                 # WAV SFX (CC0 / CC BY)
│   └── music/                  # OGG music (CC0 / CC BY)
│
├── tests/                      # Headless smoke tests (unittest)
│   └── test_smoke.py
│
├── saves/                      # Auto-created, gitignored
├── FONTS_GUIDE.md              # How to add custom fonts
├── SOUNDS_GUIDE.md             # How to add custom sounds
└── LICENSE
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.8+ |
| **Engine** | Pygame 2.0+ |
| **Persistence** | JSON (5 slots + global config) |
| **i18n** | Built-in locale manager (EN / RU + template), placeholder-safe fallback |
| **Fonts** | Bundled TTF (OFL) + automatic Cyrillic/emoji fallback |
| **UI** | Hand-rolled widgets (buttons, sliders, popups, tooltips) |
| **Effects** | Custom particle & animation systems |

Zero external Python dependencies beyond `pygame`. Everything else is written from scratch.

---

## 🧪 Tests

Headless smoke tests (no window, no audio needed):

```bash
python -m unittest discover -s tests -v
```

They cover the localization fallback (no more raw `[section.key]` placeholders
after visiting Settings), bundled fonts & emoji fallback, notification
placement/dismissal, the pause-menu layout at small resolutions, and the fact
that the click button never pulses while idle.

---

## 🌍 Adding a New Language

1. Copy `locales/lang_template.py` → `locales/lang_XX.py`
2. Fill in all translation strings
3. Restart the game — auto-detected

---

## 🔧 Customization

### Adding an upgrade
Edit `data/upgrades.py` — each upgrade is a dict with `id`, `name`, `cost`, `effect`, `category`, `branch`, and an optional `unlock` condition.

### Adding an achievement
Edit `data/achievements.py`. Secret achievements just need a `hidden: True` flag.

### Adding a random event
Edit `data/events.py` — the event system calls your handler when the event fires, so you can affect clicks, money, or spawn a golden object.

### Adding a theme
Edit `data/themes.py` — palette, font name, and background effect ID. Fonts ship with the game; drop a `.ttf` into `assets/fonts/` to use a new one (see `FONTS_GUIDE.md`).

---

## 📊 Project Stats

| Metric | Value |
|--------|-------|
| Source files | 44 |
| Lines of code | ~17,000 |
| Upgrades | 176 |
| Achievements | 50 *(6 secret)* |
| Random events | 30 |
| Themes | 13 |
| Eras | 7 |
| Languages | 2 + template |
| Save slots | 5 |

---

## 🐛 Troubleshooting

**`pygame` not found**
- `pip install -r requirements.txt` inside the venv.

**Saves not persisting**
- Make sure `saves/` is writable. Some sandboxed environments block writes to the project folder — move the project outside of a restricted path.

**Fonts look wrong on a theme**
- The game bundles its own fonts. If a `.ttf` is missing, the theme falls back to the default — re-clone to restore.

**Audio missing**
- Check `assets/sounds/` and `assets/music/`. If you replaced them with your own, verify they're `.wav` (SFX) or `.ogg` (music).

---

## 🚧 Roadmap

- ⬜ Steam-style achievement popups
- ⬜ More eras (post-space?)
- ⬜ Modding API for custom upgrade packs
- ⬜ Additional languages

---

## ⚠️ Disclaimer

This is a **hobby project**. It's a clicker game — the numbers get very large, and that's the point. It does not, in any way, teach you how to run an IT empire. Probably.

---

## 📜 License

MIT — see [LICENSE](LICENSE).

---

## 🤝 Credits

- **Creator:** [dimasbotyara](https://github.com/dimasbotyara)
- **Engine:** [Pygame](https://www.pygame.org/)
- **Fonts:** Google Fonts (OFL License)
- **Sounds:** Freesound.org (CC0 / CC BY)

---

<div align="center">

**Made with ❤️ and lots of clicking.**

**If you made it to Space Age, drop a ⭐**

</div>
