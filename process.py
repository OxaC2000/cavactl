"""Talk to the running cava process."""
import subprocess


def reload_cava():
    """Ask cava to reload its config. Return True if cava was running."""
    try:
        result = subprocess.run(
            ["pkill", "-USR1", "-x", "cava"], check=False
        )
    except FileNotFoundError:
        return False

    return result.returncode == 0
