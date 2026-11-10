"""Interactive curses interface for cavactl."""
import curses

from . import config, presets, process

# (setting, label, kind, default, options)
# int    -> options = (min, max, step)
# choice -> options = tuple of allowed values
SETTINGS = [
    ("general.bars", "Bars", "int", 20, (1, 200, 1)),
    ("general.bar_width", "Bar width", "int", 2, (1, 20, 1)),
    ("general.bar_spacing", "Bar spacing", "int", 1, (0, 20, 1)),
    ("general.framerate", "Framerate", "int", 60, (1, 240, 5)),
    ("general.sensitivity", "Sensitivity", "int", 100, (1, 500, 5)),
    ("smoothing.noise_reduction", "Noise reduction", "int", 77, (0, 100, 1)),
    ("color.gradient", "Gradient", "choice", "0", ("0", "1")),
    (
        "output.method",
        "Output method",
        "choice",
        "noncurses",
        ("noncurses", "ncurses", "sdl"),
    ),
]

HELP = "↑↓ move   ←→ change   Enter type value   p presets   e other setting   r reload   q quit"


def put(win, y, x, text, attr=0):
    height, width = win.getmaxyx()
    if y >= height or x >= width - 1:
        return
    try:
        win.addnstr(y, x, text, width - x - 1, attr)
    except curses.error:
        pass


def prompt(win, label):
    """Ask for a line of text on the bottom row."""
    height, width = win.getmaxyx()
    win.move(height - 2, 0)
    win.clrtoeol()
    put(win, height - 2, 2, label)
    win.refresh()

    curses.curs_set(1)
    curses.echo()
    try:
        raw = win.getstr(height - 2, 2 + len(label), 60)
    except curses.error:
        raw = b""
    curses.noecho()
    curses.curs_set(0)

    return raw.decode("utf-8", errors="ignore").strip()


def apply(changes, path):
    config.backup(path)
    for setting, value in changes.items():
        config.set_value(setting, value, path)

    if process.reload_cava():
        return "Saved. cava reloaded."
    return "Saved. cava is not running: applies at next start."


def to_int(value, default):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def adjust(item, current, direction):
    setting, _, kind, default, options = item

    if kind == "int":
        low, high, step = options
        base = to_int(current, default)
        return str(max(low, min(high, base + direction * step)))

    choices = list(options)
    base = current if current in choices else default
    index = (choices.index(base) + direction) % len(choices)
    return choices[index]


def preset_menu(win, path, styles):
    accent, selected, dim = styles
    names = sorted(presets.PRESETS)
    index = 0

    while True:
        win.erase()
        put(win, 0, 2, "Presets", accent)
        for row, name in enumerate(names):
            attr = selected if row == index else 0
            put(win, 2 + row, 2, f" {name:<20} ", attr)
        put(win, 3 + len(names), 2, "↑↓ move   Enter apply   q back", dim)
        win.refresh()

        key = win.getch()
        if key in (curses.KEY_UP, ord("k")):
            index = (index - 1) % len(names)
        elif key in (curses.KEY_DOWN, ord("j")):
            index = (index + 1) % len(names)
        elif key in (10, 13, curses.KEY_ENTER):
            return apply(presets.PRESETS[names[index]], path)
        elif key in (ord("q"), 27):
            return ""


def main_loop(win, path):
    curses.curs_set(0)
    curses.use_default_colors()

    accent = curses.A_BOLD
    selected = curses.A_REVERSE
    dim = curses.A_DIM

    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_MAGENTA, -1)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_MAGENTA)
        accent = curses.color_pair(1) | curses.A_BOLD
        selected = curses.color_pair(2)

    styles = (accent, selected, dim)
    index = 0
    message = ""

    while True:
        win.erase()
        height, _ = win.getmaxyx()

        put(win, 0, 2, "cavactl", accent)
        put(win, 0, 10, str(path), dim)

        for row, item in enumerate(SETTINGS):
            setting, label, _, default, _ = item
            value = config.get_value(setting, path)
            shown = value if value is not None else f"default ({default})"
            attr = selected if row == index else 0

            put(win, 2 + row, 2, f" {label:<18} {shown:<22} ", attr)
            put(win, 2 + row, 48, setting, dim)

        put(win, height - 3, 2, message, accent)
        put(win, height - 1, 2, HELP, dim)
        win.refresh()

        key = win.getch()
        item = SETTINGS[index]

        try:
            if key in (curses.KEY_UP, ord("k")):
                index = (index - 1) % len(SETTINGS)
            elif key in (curses.KEY_DOWN, ord("j")):
                index = (index + 1) % len(SETTINGS)
            elif key in (curses.KEY_LEFT, ord("h"), curses.KEY_RIGHT, ord("l")):
                direction = 1 if key in (curses.KEY_RIGHT, ord("l")) else -1
                current = config.get_value(item[0], path)
                message = apply(
                    {item[0]: adjust(item, current, direction)}, path
                )
            elif key in (10, 13, curses.KEY_ENTER):
                value = prompt(win, f"{item[1]} = ")
                if value:
                    message = apply({item[0]: value}, path)
            elif key == ord("e"):
                setting = prompt(win, "setting (section.key): ")
                if setting:
                    value = prompt(win, f"{setting} = ")
                    if value:
                        message = apply({setting: value}, path)
            elif key == ord("p"):
                message = preset_menu(win, path, styles)
            elif key == ord("r"):
                reloaded = process.reload_cava()
                message = "cava reloaded." if reloaded else "cava is not running."
            elif key in (ord("q"), 27):
                return
        except config.ConfigError as error:
            message = f"Error: {error}"


def run(path):
    config.read_lines(path)  # fail early, before curses starts
    curses.wrapper(main_loop, path)
    return 0
