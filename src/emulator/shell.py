"""Ядро эмулятора: приглашение, выполнение команд, REPL."""

import getpass
import socket

from emulator.commands import COMMANDS
from emulator.errors import ExitRequest, ShellError
from emulator.parser import parse


class Shell:
    """Командная оболочка эмулятора."""

    def __init__(self, output=print):
        """Создаёт оболочку; output — функция вывода строки."""
        self.output = output
        self.user = getpass.getuser()
        self.host = socket.gethostname()

    def prompt(self):
        """Возвращает приглашение вида user@host:~$ ."""
        return f"{self.user}@{self.host}:~$ "

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
