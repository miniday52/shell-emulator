"""Тесты REPL и базовых команд (этап 1)."""

import unittest

from tests.helpers import Capture
from emulator.errors import ExitRequest
from emulator.shell import Shell


def feeder(lines):
    """Возвращает функцию ввода, которая выдаёт строки по очереди."""
    items = iter(lines)

    def read(_prompt):
        """Возвращает очередную строку или выбрасывает EOFError."""
        try:
            return next(items)
        except StopIteration:
            raise EOFError from None
    return read


class ReplTest(unittest.TestCase):
    """Проверка диалога с пользователем."""

    def setUp(self):
        """Создаёт оболочку с перехватом вывода."""
        self.out = Capture()
        self.shell = Shell(output=self.out)

    def test_prompt_uses_os_data(self):
        """Приглашение содержит имя пользователя и хоста."""
        prompt = self.shell.prompt()
        self.assertTrue(prompt.startswith(
            f"{self.shell.user}@{self.shell.host}:"))
        self.assertTrue(prompt.endswith("$ "))

    def test_unknown_command(self):
        """Неизвестная команда — сообщение об ошибке."""
        self.assertFalse(self.shell.run_line("foo bar"))
        self.assertIn("foo: command not found", self.out.text)

    def test_exit_code(self):
        """exit завершает REPL с указанным кодом."""
        self.assertEqual(self.shell.repl(feeder(["exit 3"])), 3)

    def test_exit_bad_args(self):
        """Неверные аргументы exit."""
        self.assertFalse(self.shell.run_line("exit abc"))
        self.assertFalse(self.shell.run_line("exit 1 2"))
        self.assertIn("numeric argument required", self.out.text)
        self.assertIn("too many arguments", self.out.text)

    def test_exit_raises(self):
        """execute передаёт запрос на выход наружу."""
        with self.assertRaises(ExitRequest):
            self.shell.execute("exit")

    def test_eof_ends_repl(self):
        """Конец ввода завершает REPL с кодом 0."""
        self.assertEqual(self.shell.repl(feeder([""])), 0)


if __name__ == "__main__":
    unittest.main()
