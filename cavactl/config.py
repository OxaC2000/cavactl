"""Read and write cava's INI configuration while keeping comments."""
import os
import re
import shutil
from pathlib import Path


class ConfigError(Exception):
    """Raised when the configuration cannot be read or understood."""


def default_path():
    base = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
    return Path(base) / "cava" / "config"


def read_lines(path):
    if not path.exists():
        raise ConfigError(f"config not found: {path}")
    return path.read_text(encoding="utf-8").splitlines()


def split_key(setting):
    if "." not in setting:
        raise ConfigError("use the form section.key, e.g. general.bars")
    section, key = setting.split(".", 1)
    return section, key


def find(lines, section, key):
    """Return (header_index, active_index, commented_index)."""
    header = active = commented = None
    current = None

    for index, line in enumerate(lines):
        stripped = line.strip()
        match = re.match(r"^\[(.+)\]$", stripped)

        if match:
            current = match.group(1)
            if current == section and header is None:
                header = index
            continue

        if current != section:
            continue

        if active is None and re.match(
            rf"^{re.escape(key)}\s*=", stripped
        ):
            active = index
        elif commented is None and re.match(
            rf"^[;#]\s*{re.escape(key)}\s*=", stripped
        ):
            commented = index

    return header, active, commented


def get_value(setting, path=None):
    path = path or default_path()
    section, key = split_key(setting)
    lines = read_lines(path)
    _, active, _ = find(lines, section, key)

    if active is None:
        return None

    return lines[active].split("=", 1)[1].strip()


def set_value(setting, value, path=None):
    path = path or default_path()
    section, key = split_key(setting)
    lines = read_lines(path)
    header, active, commented = find(lines, section, key)
    new_line = f"{key} = {value}"

    if active is not None:
        lines[active] = new_line
    elif commented is not None:
        lines[commented] = new_line
    elif header is not None:
        lines.insert(header + 1, new_line)
    else:
        lines += ["", f"[{section}]", new_line]

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def list_settings(path=None):
    """Return the active settings as a list of (section.key, value)."""
    path = path or default_path()
    section = None
    settings = []

    for line in read_lines(path):
        stripped = line.strip()

        if re.match(r"^\[.+\]$", stripped):
            section = stripped[1:-1]
        elif (
            stripped
            and not stripped.startswith((";", "#"))
            and "=" in stripped
        ):
            key, value = stripped.split("=", 1)
            settings.append((f"{section}.{key.strip()}", value.strip()))

    return settings


def backup(path=None):
    """Copy the config to config.bak once, never overwriting it."""
    path = path or default_path()
    backup_path = path.with_name(path.name + ".bak")

    if path.exists() and not backup_path.exists():
        shutil.copy(path, backup_path)
