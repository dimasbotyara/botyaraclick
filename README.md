# 🖱️ botyaraclick

**From Garage to Galaxy** — A full-featured idle/clicker game built with Python & Pygame.

Start as a freelancer in a garage, click your way to building an IT empire,
and eventually launch rockets into space!

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 🎮 Features

### Core Gameplay
- 🖱️ **Click to earn** — Write code, earn dollars, build your empire
- 💰 **176+ upgrades** across 6 categories and 23 branches
- 👥 **Hire staff** for passive income (interns → AI engineers)
- 🏢 **7 eras of progression** (Garage → Home Office → Startup → IT Company → Corporation → Megacorp → Space Age)
- ⭐ **Prestige system** — Reset for permanent bonuses (Reputation Points)
- 🎲 **30 random events** — Golden objects, market booms, crises, challenges, investor deals

### Visual Polish
- ✨ **Particle effects** — Sparks, coins, confetti, stars
- 💥 **Click animations** — Spring bounce, screen shake, floating numbers
- 🎨 **13 themes** — Cyberpunk, Cozy Forest, Retro 8-bit, Royal Gold, Deep Space, and more
- 🌧️ **Background effects** — Matrix rain, snowflakes, falling leaves, bubbles, embers, bats
- 🏆 **50 achievements** with small bonuses (including 6 secret ones!)

### Quality of Life
- 💾 **5 save slots** with auto-save every 30 seconds
- 🌐 **Localization** — English & Russian included, easy to add more
- ⚙️ **Full settings** — Audio, visuals, number formats, effects toggle
- 🔊 **Sound system** — SFX + music with separate volume controls
- 📊 **Detailed statistics**
- 🖥️ **Fullscreen & windowed** mode (F11 to toggle)

---

## 🚀 Quick Start

### 1. Clone / Download

```bash
git clone https://github.com/dimasbotyara/botyaraclick.git
cd botyaraclick
```

### 2. Install pygame

```bash
pip install -r requirements.txt
```

### 3. Run

```bash
python main.py
```

That's it! **Everything is included** — fonts, sounds, music are all
bundled with the project. No extra downloads needed.

---

## 📁 Project Structure

```
botyaraclick/
│
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
│   ├── language_select.py      # Language selection
│   ├── main_menu.py            # Main menu
│   ├── save_load.py            # Save slot selection
│   ├── settings.py             # Settings
│   ├── game_screen.py          # Main gameplay
│   ├── pause_menu.py           # Pause menu
│   ├── upgrade_tree.py         # Upgrade tree
│   ├── themes_shop.py          # Theme shop
│   └── prestige_screen.py      # Prestige
│
├── ui/                         # UI components
│   ├── button.py               # Buttons
│   ├── panel.py                # Panels & overlays
│   ├── scrollbar.py            # Scroll areas
│   ├── slider.py               # Sliders
│   ├── tooltip.py              # Tooltips
│   ├── notification.py         # Notifications
│   └── popup.py                # Popup dialogs
│
├── effects/                    # Visual effects
│   ├── particles.py            # Particle system
│   ├── floating_text.py        # Floating numbers
│   ├── animations.py           # Animations
│   └── bg_effects.py           # Background effects
│
├── locales/                    # Localization
│   ├── locale_manager.py       # Auto-detection locale manager
│   ├── lang_en.py              # English
│   ├── lang_ru.py              # Russian
│   └── lang_template.py        # Template for new languages
│
├── assets/                     # All assets included!
│   ├── fonts/                  # TTF fonts (OFL license)
│   ├── sounds/                 # WAV sound effects (CC0/CC BY)
│   └── music/                  # OGG music (CC0/CC BY)
│
└── saves/                      # Auto-created, gitignored
```

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

| # | Theme | Font | Background Effect |
|---|-------|------|-------------------|
| 1 | Business (Default) | Montserrat | None |
| 2 | Cyberpunk / Neon | Orbitron | Matrix Rain |
| 3 | Cozy Forest | Comfortaa | Falling Leaves |
| 4 | Retro 8-bit | Pixelify Sans | Scanlines |
| 5 | Royal Gold | Cinzel | Gold Sparkle |
| 6 | Deep Space | Exo 2 | Stars |
| 7 | Candy Land | Sniglet | Bubbles |
| 8 | Hacker / Terminal | Fira Code | Matrix Rain |
| 9 | Minimalism | Montserrat | None |
| 10 | Deep Ocean | Bubblegum Sans | Bubbles |
| 11 | Infernal | Rubik Glitch | Embers |
| 12 | Halloween | Creepster | Bats |
| 13 | Winter Wonderland | Caveat | Snowflakes |

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

## ⭐ Prestige System

Once you've earned **$500M total**, you can **Prestige**:
- All money and upgrades reset
- You earn **Reputation Points (RP)**
- RP formula: `floor(√(total_earned / 500,000,000))`
- Spend RP on permanent bonuses
- Achievements, prestige upgrades, and statistics are preserved

---

## 🌍 Adding a New Language

1. Copy `locales/lang_template.py` → `locales/lang_XX.py`
2. Fill in all translation strings
3. Restart — auto-detected!

---

## 📊 Project Stats

| Metric | Value |
|--------|-------|
| Source files | 49 |
| Lines of code | ~15,000 |
| Upgrades | 176 |
| Achievements | 50 |
| Events | 30 |
| Themes | 13 |
| Eras | 7 |
| Languages | 2 + template |

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🤝 Credits

- **Creator:** [dimasbotyara](https://github.com/dimasbotyara)
- **Engine:** [Pygame](https://www.pygame.org/)
- **Fonts:** Google Fonts ([OFL License](https://scripts.sil.org/OFL))
- **Sounds:** [Freesound.org](https://freesound.org/) (CC0 / CC BY)

---

Made with ❤️ and lots of clicking.
