"""Command-line interface of cavactl."""
import argparse
import sys
from pathlib import Path

from . import __version__, config, presets, process


def build_parser():
    parser = argparse.ArgumentParser(
        prog="cavactl",
        description="Edit cava's configuration from the command line.",
    )
    parser.add_argument(
        "--version", action="version", version=f"cavactl {__version__}"
    )
    parser.add_argument(
        "--config", type=Path, help="path to the cava config file"
    )

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("tui", help="open the interactive interface (default)")
    sub.add_parser("list", help="show active settings")

    p_get = sub.add_parser("get", help="read a setting")
    p_get.add_argument("setting", help="e.g. general.bars")

    p_set = sub.add_parser("set", help="change a setting")
    p_set.add_argument("setting", help="e.g. general.bars")
    p_set.add_argument("value")

    p_preset = sub.add_parser("preset", help="apply a preset")
    p_preset.add_argument("name", choices=sorted(presets.PRESETS))

    sub.add_parser("reload", help="ask cava to reload its config")

    return parser


def reload_and_report():
    if not process.reload_cava():
        print("cava is not running: changes apply at next start.")


def run(args, path):
    if args.command in (None, "tui"):
        from . import tui

        return tui.run(path)

    if args.command == "list":
        for setting, value in config.list_settings(path):
            print(f"{setting} = {value}")
        return 0

    if args.command == "get":
        value = config.get_value(args.setting, path)
        if value is None:
            print("(not set)", file=sys.stderr)
            return 1
        print(value)
        return 0

    if args.command == "set":
        config.backup(path)
        config.set_value(args.setting, args.value, path)
        reload_and_report()
        return 0

    if args.command == "preset":
        config.backup(path)
        for setting, value in presets.PRESETS[args.name].items():
            config.set_value(setting, value, path)
        reload_and_report()
        return 0

    if args.command == "reload":
        reload_and_report()
        return 0

    return 1


def main(argv=None):
    args = build_parser().parse_args(argv)
    path = args.config or config.default_path()

    try:
        return run(args, path)
    except config.ConfigError as error:
        print(f"cavactl: {error}", file=sys.stderr)
        return 1
