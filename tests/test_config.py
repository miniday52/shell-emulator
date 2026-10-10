"""Тесты параметров командной строки и стартового скрипта (этап 2)."""

import os
import tempfile
import unittest

from tests.helpers import Capture
from emulator.config import dump_config, parse_args
from emulator.errors import ExitRequest, ShellError
from emulator.shell import Shell


class ConfigTest(unittest.TestCase):
    """Проверка разбора параметров."""

    def test_defaults(self):
        """Без параметров значения не заданы."""
        config = parse_args([])
        self.assertIsNone(config.vfs)
        self.assertIsNone(config.script)

    def test_all_options(self):
        """Оба параметра разбираются."""
        config = parse_args(["--vfs", "a.xml", "--script", "s.txt"])
        self.assertEqual((config.vfs, config.script), ("a.xml", "s.txt"))

    def test_dump(self):
        """Отладочный вывод содержит все параметры."""
        out = Capture()
        dump_config(parse_args(["--vfs", "a.xml"]), out)
        self.assertIn("vfs = a.xml", out.text)
        self.assertIn("script = <не задан>", out.text)


class ScriptTest(unittest.TestCase):
    """Проверка выполнения стартового скрипта."""

    def setUp(self):
        """Создаёт оболочку и временный файл скрипта."""
        self.out = Capture()
        self.shell = Shell(output=self.out)
        handle, self.path = tempfile.mkstemp(suffix=".txt")
        os.close(handle)

    def tearDown(self):
        """Удаляет временный файл."""
        os.remove(self.path)

    def write(self, text):
        """Записывает текст скрипта."""
        with open(self.path, "w", encoding="utf-8") as file:
            file.write(text)

    def test_errors_are_skipped(self):
        """Ошибочные строки пропускаются, выполнение продолжается."""
        self.write("# comment\nbad\n\npwd\nexit oops\n")
        self.assertEqual(self.shell.run_script(self.path), 2)
        self.assertIn(":2: line skipped", self.out.text)
        self.assertIn(":5: line skipped", self.out.text)
        self.assertIn("$ pwd", self.out.text)

    def test_exit_stops_script(self):
        """exit в скрипте завершает работу."""
        self.write("exit 7\ncd never\n")
        with self.assertRaises(ExitRequest) as context:
            self.shell.run_script(self.path)
        self.assertEqual(context.exception.code, 7)
        self.assertNotIn("never", self.out.text)

    def test_missing_script(self):
        """Отсутствующий скрипт — ошибка."""
        with self.assertRaises(ShellError):
            self.shell.run_script(self.path + ".missing")


if __name__ == "__main__":
    unittest.main()
