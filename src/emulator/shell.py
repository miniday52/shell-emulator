"""Ядро эмулятора: приглашение, выполнение команд, REPL."""

import getpass
import socket

from emulator.commands import COMMANDS
from emulator.errors import ExitRequest, ShellError
from emulator.parser import parse
from emulator.vfs import SEPARATOR, default_vfs


class Shell:
    """Командная оболочка эмулятора."""

    def __init__(self, vfs=None, output=print):
        """Создаёт оболочку над VFS; output — функция вывода строки.

        Если VFS не передана, создаётся VFS по умолчанию в памяти.
        """
        self.output = output
        self.user = getpass.getuser()
        self.host = socket.gethostname()
        self.vfs = vfs if vfs is not None else default_vfs()
        self.cwd = self.vfs.resolve(self.vfs.root, self.vfs.home)

    def display_path(self):
        """Текущий путь для приглашения; домашний каталог — ~."""
        path, home = self.cwd.path, self.vfs.home
        if home == SEPARATOR:
            return path
        if path == home:
            return "~"
        if path.startswith(home + SEPARATOR):
            return "~" + path[len(home):]
        return path

    def prompt(self):
        """Возвращает приглашение вида user@host:~$ ."""
        return f"{self.user}@{self.host}:{self.display_path()}$ "

    def execute(self, line):
        """Выполняет одну строку. Ошибки выбрасываются как ShellError."""
        name, args = parse(line)
        if name is None:
            return
        handler = COMMANDS.get(name)
        if handler is None:
            raise ShellError(f"{name}: command not found")
        handler(self, args)

    def run_line(self, line):
        """Выполняет строку и сообщает об ошибке. Возвращает успех."""
        try:
            self.execute(line)
        except ShellError as error:
            self.output(f"error: {error}")
            return False
        return True

    def run_script(self, path):
        """Выполняет стартовый скрипт построчно.

        Ввод и вывод отображаются как диалог с пользователем. Ошибочные
        строки пропускаются с сообщением об ошибке. Пустые строки и
        комментарии (#) игнорируются. Возвращает число ошибочных строк.
        """
        try:
            with open(path, encoding="utf-8-sig") as file:
                lines = file.read().splitlines()
        except OSError as error:
            raise ShellError(
                f"cannot read script '{path}': {error.strerror}") from None
        failed = 0
        for number, line in enumerate(lines, start=1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            self.output(self.prompt() + line)
            if not self.run_line(line):
                failed += 1
                self.output(f"[script] {path}:{number}: line skipped")
        return failed

    def repl(self, read=input):
        """Интерактивный цикл чтения-выполнения. Возвращает код выхода."""
        while True:
            try:
                line = read(self.prompt())
            except EOFError:
                self.output("")
                return 0
            except KeyboardInterrupt:
                self.output("^C")
                continue
            try:
                self.run_line(line)
            except ExitRequest as request:
                return request.code
