"""
botyaraclick - main.py
Entry point.

Run:
    python main.py

Requirements:
    - Python 3.8+
    - pygame 2.0+

Author: dimasbotyara
License: MIT
"""

import sys
import os

# Working directory = script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Main entry point."""
    try:
        import pygame
    except ImportError:
        print("=" * 50)
        print("ERROR: pygame is not installed!")
        print("Install it with: pip install pygame")
        print("=" * 50)
        sys.exit(1)

    # Check pygame version
    try:
        pygame_version = tuple(int(x) for x in pygame.version.ver.split('.')[:2])
        if pygame_version < (2, 0):
            print(f"WARNING: pygame {pygame.version.ver} detected.")
            print("botyaraclick works best with pygame 2.0+")
            print("Update with: pip install --upgrade pygame")
    except (ValueError, AttributeError):
        pass

    # Ensure required directories exist
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for subdir in ["assets/fonts", "assets/sounds", "assets/music",
                    "saves", "locales"]:
        os.makedirs(os.path.join(base_dir, subdir), exist_ok=True)

    # Check locales
    locales_dir = os.path.join(base_dir, "locales")
    lang_files = [f for f in os.listdir(locales_dir)
                  if f.startswith("lang_") and f.endswith(".py")]

    if not lang_files:
        print("ERROR: No language files found in locales/")
        print("Need at least lang_en.py or lang_ru.py")
        sys.exit(1)

    langs = ', '.join(f[5:-3] for f in lang_files)
    print(f"botyaraclick starting... ({len(lang_files)} language(s): {langs})")

    # Run game
    game = None
    try:
        from game import Game
        game = Game()
        game.run()
    except KeyboardInterrupt:
        print("\nGame interrupted by user.")
    except Exception as e:
        print(f"\n{'=' * 50}")
        print(f"FATAL ERROR: {e}")
        print(f"{'=' * 50}")
        import traceback
        traceback.print_exc()

        # Try to save before crash
        try:
            if game and hasattr(game, 'save_manager'):
                if game.save_manager.save_data:
                    game.save_manager.save_current()
                game.save_manager.save_global()
                print("\nGame progress saved before crash.")
        except Exception:
            pass

        sys.exit(1)
    finally:
        try:
            pygame.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
