"""Точка входа: python -m emulator [--vfs PATH] [--script PATH]."""

import sys

from emulator.config import dump_config, parse_args
from emulator.errors import ExitRequest, ShellError
from emulator.shell import Shell


def main(argv=None):
    """Запускает эмулятор: стартовый скрипт, затем интерактивный режим."""
    config = parse_args(argv)
    shell = Shell()
    dump_config(config, shell.output)
    try:
        if config.script:
            failed = shell.run_script(config.script)
            if failed:
                shell.output(f"[script] finished with {failed} error(s)")
        return shell.repl()
    except ExitRequest as request:
        return request.code
    except ShellError as error:
        shell.output(f"error: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
