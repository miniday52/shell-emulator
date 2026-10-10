"""Точка входа: python -m emulator."""

import sys

from emulator.shell import Shell


def main():
    """Запускает эмулятор в интерактивном режиме."""
    return Shell().repl()


if __name__ == "__main__":
    sys.exit(main())
