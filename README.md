# cavactl

A small CLI to edit [cava](https://github.com/karlstav/cava)'s configuration and reload it live.

cava has no plugin system: its settings live in an INI file and it reloads
that file when it receives `SIGUSR1`. `cavactl` edits the file (keeping your
comments) and sends the signal for you.

## Install

```bash
git clone https://github.com/OxaC2000/cavactl.git
cd cavactl
pip install --user .
```

## Usage

```bash
cavactl list                    # show active settings
cavactl get general.bars        # read a setting
cavactl set general.bars 40     # change a setting
cavactl preset tokyonight       # apply a preset
cavactl reload                  # ask cava to reload
```

Use `--config PATH` to target another config file.
A backup is saved once as `config.bak` before the first change.

## Presets

| Name | Effect |
|---|---|
| `tokyonight` | Blue to purple gradient |
| `minimal` | 32 bars, strong smoothing |

## Development

```bash
pip install pytest
python -m pytest
```

## License

MIT
