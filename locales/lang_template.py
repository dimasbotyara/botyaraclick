"""
botyaraclick - Language Template

HOW TO ADD A NEW LANGUAGE:
1. Copy this file
2. Rename it to lang_XX.py where XX is your language code
   (e.g., lang_de.py for German, lang_fr.py for French)
3. Fill in all the strings with translations
4. The game will automatically detect the new language file!

IMPORTANT:
- Do NOT change the keys (left side of ":")
- Do NOT remove any keys
- Keep {value}, {amount}, {count}, etc. placeholders — they will be
  replaced with actual values
- The "_language_name" value will be shown in the language selection screen
"""

STRINGS = {
    # Meta — CHANGE THESE:
    "_language_name": "YOUR LANGUAGE NAME HERE",  # e.g., "Deutsch", "Français"
    "_language_code": "xx",  # e.g., "de", "fr", "es"
    "_author": "Your Name",

    # === MAIN MENU ===
    "menu": {
        "title": "botyaraclick",  # Don't translate the game name!
        "play": "",
        "continue": "",
        "settings": "",
        "quit": "",
        "new_game": "",
        "load_game": "",
        "select_slot": "",
        "slot": "Slot {num}",  # Keep {num}!
        "empty_slot": "",
        "delete_save": "",
        "delete_confirm": "",
        "yes": "",
        "no": "",
        "cancel": "",
        "back": "",
    },

    # === GAME SCREEN ===
    "game": {
        "click": "",
        "per_click": "",
        "per_second": "",
        "balance": "",
        "total_earned": "",
        "era": "",
        "prestige_available": "",
    },

    # === PAUSE ===
    "pause": {
        "title": "",
        "resume": "",
        "save": "",
        "save_success": "",
        "statistics": "",
        "achievements": "",
        "settings": "",
        "main_menu": "",
        "confirm_quit": "",
        "unsaved_warning": "",
        "save_and_quit": "",
        "quit_no_save": "",
    },

    # Continue translating all sections from lang_en.py ...
    # Copy the full structure from lang_en.py and replace English
    # strings with your translations.

    # TIP: You can use lang_en.py as reference for all keys needed.
}
