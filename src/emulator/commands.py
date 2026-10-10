"""Реализация команд эмулятора."""

import itertools
import time

from emulator.errors import ExitRequest, ShellError
from emulator.options import split_options

MAX_EXIT_ARGS = 1
MAX_CD_ARGS = 1
SINGLE = 1
COUNT_WIDTH = 7
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400
DIR_MODE = "drwxr-xr-x"
FILE_MODE = "-rw-r--r--"


def resolve_or_fail(shell, command, path):
    """Находит узел VFS по пути или выбрасывает ShellError."""
    node = shell.vfs.resolve(shell.cwd, path)
    if node is None:
        raise ShellError(f"{command}: {path}: No such file or directory")
    return node


def _ls_entry(node, name, long_format):
    """Форматирует одну запись вывода ls."""
    if not long_format:
        return name
    if node.is_dir:
        return f"{DIR_MODE} {len(node.children):>8} {name}"
    return f"{FILE_MODE} {node.size:>8} {name}"


def _ls_node(node, flags):
    """Возвращает строки вывода ls для одного узла."""
    long_format = "l" in flags
    if not node.is_dir:
        return [_ls_entry(node, node.name, long_format)]
    entries = []
    if "a" in flags:
        parent = node.parent if node.parent is not None else node
        entries += [(".", node), ("..", parent)]
    entries += sorted(node.children.items())
    lines = [_ls_entry(child, name, long_format)
             for name, child in entries]
    if long_format:
        return [f"total {len(node.children)}"] + lines
    return ["  ".join(lines)] if lines else []


def cmd_ls(shell, args):
    """ls [-l] [-a] [путь...]: выводит содержимое каталогов."""
    flags, paths = split_options("ls", args, "la")
    paths = paths or ["."]
    errors = []
    for path in paths:
        node = shell.vfs.resolve(shell.cwd, path)
        if node is None:
            errors.append(f"ls: cannot access '{path}': "
                          "No such file or directory")
            continue
        if len(paths) > SINGLE and node.is_dir:
            shell.output(f"{path}:")
        for line in _ls_node(node, flags):
            shell.output(line)
    if errors:
        raise ShellError("; ".join(errors))


def cmd_cd(shell, args):
    """cd [путь|-]: меняет текущий каталог (без аргумента — домой)."""
    if len(args) > MAX_CD_ARGS:
        raise ShellError("cd: too many arguments")
    target = args[0] if args else "~"
    if target == "-":
        if shell.previous_dir is None:
            raise ShellError("cd: OLDPWD not set")
        node = shell.previous_dir
        shell.output(node.path)
    else:
        node = resolve_or_fail(shell, "cd", target)
    if not node.is_dir:
        raise ShellError(f"cd: {target}: Not a directory")
    shell.previous_dir, shell.cwd = shell.cwd, node


def cmd_pwd(shell, args):
    """pwd: выводит абсолютный путь текущего каталога."""
    if args:
        raise ShellError("pwd: too many arguments")
    shell.output(shell.cwd.path)


def _format_duration(seconds):
    """Форматирует длительность в стиле uptime: '1 day, 2:05'."""
    days, rest = divmod(int(seconds), SECONDS_PER_DAY)
    hours, rest = divmod(rest, SECONDS_PER_HOUR)
    minutes = rest // SECONDS_PER_MINUTE
    clock = f"{hours}:{minutes:02d}" if hours else f"{minutes} min"
    if not days:
        return clock
    suffix = "day" if days == SINGLE else "days"
    return f"{days} {suffix}, {clock}"


def _pretty_duration(seconds):
    """Форматирует длительность для uptime -p."""
    minutes = int(seconds) // SECONDS_PER_MINUTE
    hours, minutes = divmod(minutes, SECONDS_PER_MINUTE)
    parts = []
    if hours:
        parts.append(f"{hours} hour" + ("" if hours == SINGLE else "s"))
    parts.append(f"{minutes} minute" + ("" if minutes == SINGLE else "s"))
    return "up " + ", ".join(parts)


def cmd_uptime(shell, args):
    """uptime [-p] [-s]: время работы эмулятора."""
    flags, operands = split_options("uptime", args, "ps")
    if operands:
        raise ShellError(f"uptime: extra operand '{operands[0]}'")
    elapsed = time.time() - shell.start_time
    if "s" in flags:
        started = time.localtime(shell.start_time)
        shell.output(time.strftime("%Y-%m-%d %H:%M:%S", started))
    elif "p" in flags:
        shell.output(_pretty_duration(elapsed))
    else:
        now = time.strftime("%H:%M:%S")
        shell.output(f" {now} up {_format_duration(elapsed)},  1 user,"
                     "  load average: 0.00, 0.00, 0.00")


def _read_text(shell, command, path):
    """Читает файл VFS как текст UTF-8."""
    node = resolve_or_fail(shell, command, path)
    if node.is_dir:
        raise ShellError(f"{command}: {path}: Is a directory")
    return node.data.decode("utf-8", errors="replace")


def _uniq_groups(lines, ignore_case):
    """Группирует соседние одинаковые строки: [(строка, количество)]."""
    key = str.lower if ignore_case else None
    return [(group[0], len(group)) for group in
            (list(items) for _, items in itertools.groupby(lines, key))]


def cmd_uniq(shell, args):
    """uniq [-c] [-d] [-u] [-i] файл: удаляет соседние повторы строк."""
    flags, operands = split_options("uniq", args, "cdui")
    if not operands:
        raise ShellError("uniq: missing file operand")
    if len(operands) > SINGLE:
        raise ShellError(f"uniq: extra operand '{operands[1]}'")
    lines = _read_text(shell, "uniq", operands[0]).splitlines()
    for line, count in _uniq_groups(lines, "i" in flags):
        if "d" in flags and count == SINGLE:
            continue
        if "u" in flags and count > SINGLE:
            continue
        prefix = f"{count:>{COUNT_WIDTH}} " if "c" in flags else ""
        shell.output(prefix + line)


def _is_inside(node, ancestor):
    """Проверяет, что node совпадает с ancestor или вложен в него."""
    while node is not None:
        if node is ancestor:
            return True
        node = node.parent
    return False


def _rm_problem(shell, path, node, flags):
    """Возвращает причину, по которой удалить узел нельзя, или None."""
    if path.rstrip("/").split("/")[-1] in (".", ".."):
        return f"refusing to remove '.' or '..' directory: skipping '{path}'"
    if node.parent is None:
        return "it is dangerous to operate recursively on '/'"
    if _is_inside(shell.cwd, node):
        return f"cannot remove '{path}': current directory is inside"
    if node.is_dir and "r" not in flags:
        if "d" not in flags:
            return f"cannot remove '{path}': Is a directory"
        if node.children:
            return f"cannot remove '{path}': Directory not empty"
    return None


def _rm_one(shell, path, flags):
    """Удаляет один путь; возвращает сообщение об ошибке или None."""
    node = shell.vfs.resolve(shell.cwd, path)
    if node is None:
        if "f" in flags:
            return None
        return f"cannot remove '{path}': No such file or directory"
    problem = _rm_problem(shell, path, node, flags)
    if problem is not None:
        return problem
    del node.parent.children[node.name]
    node.parent = None
    if shell.previous_dir is not None and _is_inside(
            shell.previous_dir, node):
        shell.previous_dir = None
    if "v" in flags:
        kind = "directory " if node.is_dir else ""
        shell.output(f"removed {kind}'{path}'")
    return None


def cmd_rm(shell, args):
    """rm [-r|-R] [-f] [-d] [-v] путь...: удаляет файлы и каталоги.

    Изменения выполняются только в памяти, источник VFS не меняется.
    """
    flags, paths = split_options("rm", args, "rRfdv")
    if "R" in flags:
        flags.add("r")
    if not paths:
        if "f" in flags:
            return
        raise ShellError("rm: missing operand")
    errors = [error for error in
              (_rm_one(shell, path, flags) for path in paths) if error]
    if errors:
        raise ShellError("; ".join(f"rm: {error}" for error in errors))


def cmd_exit(shell, args):
    """Завершает работу эмулятора: exit [код]."""
    if len(args) > MAX_EXIT_ARGS:
        raise ShellError("exit: too many arguments")
    if not args:
        raise ExitRequest(0)
    try:
        code = int(args[0])
    except ValueError:
        raise ShellError(
            f"exit: {args[0]}: numeric argument required") from None
    raise ExitRequest(code)


def cmd_vfs_info(shell, args):
    """Служебная команда: сведения о загруженной VFS."""
    if args:
        raise ShellError("vfs-info: too many arguments")
    vfs = shell.vfs
    dirs, files, total = vfs.stats()
    shell.output(f"name: {vfs.name}")
    shell.output(f"source: {vfs.source or '<in-memory default>'}")
    shell.output(f"home: {vfs.home}")
    shell.output(f"directories: {dirs}, files: {files}, bytes: {total}")


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "pwd": cmd_pwd,
    "uptime": cmd_uptime,
    "uniq": cmd_uniq,
    "rm": cmd_rm,
    "exit": cmd_exit,
    "vfs-info": cmd_vfs_info,
}
