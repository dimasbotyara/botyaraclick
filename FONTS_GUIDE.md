# 🔤 Шрифты в botyaraclick

## Коротко

**Все шрифты уже лежат в репозитории.** Ничего скачивать не нужно — игра
полностью офлайн. Папка: `assets/fonts/`.

```
assets/fonts/
├── Montserrat-Regular.ttf      # базовая тема + фолбэк для кириллицы
├── Montserrat-Bold.ttf
├── NotoEmoji-Regular.ttf       # ЭМОДЗИ 🚀 🏆 🤮 ⏸ ✨
├── Orbitron-Regular.ttf / -Bold.ttf
├── Comfortaa-Regular.ttf / -Bold.ttf
├── PixelifySans-Regular.ttf / -Bold.ttf
├── Cinzel-Regular.ttf / -Bold.ttf
├── Exo2-Regular.ttf / -Bold.ttf
├── Sniglet-Regular.ttf / -Bold.ttf
├── FiraCode-Regular.ttf / -Bold.ttf
├── BubblegumSans-Regular.ttf
├── RubikGlitch-Regular.ttf
├── Creepster-Regular.ttf
├── Caveat-Regular.ttf / -Bold.ttf
└── licenses/                   # тексты лицензий OFL (обязательны при раздаче)
```

## Как это работает

`ui/fonts.py` содержит `FallbackFont` — обёртку над `pygame.font.Font`.

pygame сам **не умеет** подставлять глифы из другого шрифта: если в шрифте
темы нет символа, рисуется «тофу» ▯. Поэтому `FallbackFont`:

1. режет строку на кластеры (буква / эмодзи / составное эмодзи 👨‍👩‍👧 / флаг 🇷🇺);
2. читает таблицу `cmap` каждого шрифта и смотрит, где реально есть нужный символ;
3. рисует каждый кусок «своим» шрифтом и склеивает результат по базовой линии.

Порядок поиска глифа:

| Приоритет | Шрифт | Зачем |
|---|---|---|
| 1 | шрифт темы (Orbitron, Cinzel, …) | основной стиль |
| 2 | **Montserrat** | кириллица, которой нет в латинских шрифтах |
| 3 | **NotoEmoji-Regular.ttf** | эмодзи (монохромные, тонируются цветом текста) |

Результат: «Привет 🚀 мир» в теме Cyberpunk рисуется как
Orbitron («Hello») + Montserrat («Привет мир») + Noto Emoji («🚀»).

> Эмодзи специально **монохромные**: SDL_ttf 2.20 (внутри pygame 2.6) не
> умеет рендерить цветные CBDT-шрифты вроде NotoColorEmoji. Монохромные
> отлично масштабируются, не «мылятся» и красятся в цвет текста.

## Использование в коде

```python
from ui.fonts import get_font, load_theme_fonts

font = get_font(24)                    # обычный
font = get_font(42, bold=True)         # жирный
font = get_font(14, family="FiraCode") # конкретная тема

# Готовый набор для экрана (title/large/normal/small/tiny/...)
fonts = load_theme_fonts("Montserrat")
```

Шрифты кешируются по `(family, bold, size)`, отрисованные строки — тоже,
поэтому в игровом цикле это не тормозит (2000 строк ≈ 0.16 с суммарно).

## Список семейств и тем

| Семейство | Файлы | Кириллица |
|---|---|---|
| Montserrat (default, Minimalism) | `Montserrat-{Regular,Bold}.ttf` | ✅ |
| Orbitron (Cyberpunk) | `Orbitron-{Regular,Bold}.ttf` | — (фолбэк) |
| Comfortaa (Cozy Forest) | `Comfortaa-{Regular,Bold}.ttf` | ✅ |
| PixelifySans (Retro 8-bit) | `PixelifySans-{Regular,Bold}.ttf` | — (фолбэк) |
| Cinzel (Royal Gold) | `Cinzel-{Regular,Bold}.ttf` | — (фолбэк) |
| Exo2 (Deep Space) | `Exo2-{Regular,Bold}.ttf` | ✅ |
| Sniglet (Candy Land) | `Sniglet-{Regular,Bold}.ttf` | — (фолбэк) |
| FiraCode (Hacker) | `FiraCode-{Regular,Bold}.ttf` | ✅ |
| BubblegumSans (Deep Ocean) | `BubblegumSans-Regular.ttf` | — (фолбэк) |
| RubikGlitch (Infernal) | `RubikGlitch-Regular.ttf` | — (фолбэк) |
| Creepster (Halloween) | `Creepster-Regular.ttf` | — (фолбэк) |
| Caveat (Winter) | `Caveat-{Regular,Bold}.ttf` | ✅ |

Даже если у шрифта темы нет кириллицы, русский текст всё равно читается —
за счёт второго слоя фолбэка.

## Источники и лицензии

Все шрифты — **SIL Open Font License 1.1** (можно использовать и
распространять бесплатно, в том числе в коммерческих проектах).

Источник: [Google Fonts](https://github.com/google/fonts) (репозиторий
`google/fonts`, каталог `ofl/<family>/`).

Вариативные шрифты (`Montserrat[wght].ttf`, `Orbitron[wght].ttf`, …) были
разложены на статические начертания Regular (400) и Bold (700) через
`fontTools.varLib.instancer`, чтобы pygame корректно рисовал жирный текст.

Тексты лицензий лежат в `assets/fonts/licenses/*-OFL.txt` — их нужно
сохранять при распространении игры.

## Добавить свой шрифт

1. Положите `.ttf` в `assets/fonts/`.
2. Добавьте семейство в `THEME_FONTS` в `data/themes.py`:

```python
"Montserrat": {"regular": "Montserrat-Regular.ttf", "bold": "Montserrat-Bold.ttf"},
"MyFont":     {"regular": "MyFont-Regular.ttf",     "bold": "MyFont-Bold.ttf"},
```

3. Укажите `"font_file": "MyFont"` у нужной темы.

Эмодзи и кириллица подхватятся автоматически — фолбэк общий для всех тем.
