"""Разбор параметров командной строки эмулятора."""

import argparse


def build_arg_parser():
    """Создаёт парсер параметров командной строки."""
    parser = argparse.ArgumentParser(
        prog="emulator",
        description="Эмулятор командной оболочки UNIX-подобной ОС.")
    parser.add_argument(
        "--vfs", metavar="PATH", default=None,
        help="путь к физическому расположению VFS (XML-файл)")
    parser.add_argument(
        "--script", metavar="PATH", default=None,
        help="путь к стартовому скрипту")
    return parser


def parse_args(argv=None):
    """Разбирает параметры командной строки."""
    return build_arg_parser().parse_args(argv)


def dump_config(config, output):
    """Отладочный вывод всех заданных параметров эмулятора."""
    output("[config] Параметры эмулятора:")
    for key, value in sorted(vars(config).items()):
        shown = value if value is not None else "<не задан>"
        output(f"[config]   {key} = {shown}")
