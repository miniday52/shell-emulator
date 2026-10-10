"""Тесты команды rm (этап 5)."""

import unittest

from tests.test_commands import DEEP, CommandTestCase
from emulator.vfs import load_vfs


class RmTest(CommandTestCase):
    """rm изменяет VFS только в памяти."""

    def exists(self, path):
        """Проверяет наличие узла в VFS."""
        return self.shell.vfs.resolve(self.shell.vfs.root, path) is not None

    def test_remove_file(self):
        """Удаление файла, исходный XML не меняется."""
        self.run_ok("rm /etc/motd")
        self.assertFalse(self.exists("/etc/motd"))
        self.assertIsNotNone(load_vfs(DEEP).resolve(None, "/etc/motd"))

    def test_verbose_and_several(self):
        """Несколько операндов и -v."""
        text = self.run_ok("rm -v /etc/motd /etc/hostname")
        self.assertIn("removed '/etc/motd'", text)
        self.assertEqual(self.run_ok("ls /etc"), "")

    def test_partial_failure(self):
        """Существующие операнды удаляются, об отсутствующих — ошибка."""
        self.assertIn("No such file", self.run_fail("rm /nope /etc/motd"))
        self.assertFalse(self.exists("/etc/motd"))

    def test_force(self):
        """-f подавляет ошибки отсутствия и пустой список операндов."""
        self.run_ok("rm -f /nope")
        self.run_ok("rm -f")
        self.assertIn("missing operand", self.run_fail("rm"))

    def test_directories(self):
        """Каталог: без -r ошибка, -d только для пустых, -r/-R рекурсивно."""
        self.assertIn("Is a directory", self.run_fail("rm /tmp"))
        self.run_ok("rm -d /tmp")
        self.assertIn("not empty", self.run_fail("rm -d /etc"))
        self.assertIn("removed directory", self.run_ok("rm -rv /etc"))
        self.run_ok("rm -R projects")
        self.assertFalse(self.exists("/etc"))
        self.assertEqual(self.run_ok("ls"), "notes.txt")

    def test_protection(self):
        """Нельзя удалить корень, . и .., текущий каталог и его предков."""
        self.assertIn("dangerous", self.run_fail("rm -r /"))
        self.assertIn("refusing", self.run_fail("rm -r ."))
        self.assertIn("refusing", self.run_fail("rm -r projects/.."))
        self.assertIn("current directory", self.run_fail("rm -r /home"))
        self.assertTrue(self.exists("/home/user"))

    def test_previous_dir_cleared(self):
        """Удаление предыдущего каталога сбрасывает cd -."""
        self.run_ok("cd /var/log")
        self.run_ok("cd /")
        self.run_ok("rm -r var")
        self.assertIn("OLDPWD", self.run_fail("cd -"))

    def test_invalid_option(self):
        """Неверная опция."""
        self.assertIn("invalid option", self.run_fail("rm -x a"))


if __name__ == "__main__":
    unittest.main()
