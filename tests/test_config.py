from cavactl import config

SAMPLE = """[general]
; bars = 0
bars = 20

[color]
;gradient = 0
"""


def make_config(tmp_path):
    path = tmp_path / "config"
    path.write_text(SAMPLE, encoding="utf-8")
    return path


def test_get_active_value(tmp_path):
    path = make_config(tmp_path)
    assert config.get_value("general.bars", path) == "20"


def test_get_missing_value(tmp_path):
    path = make_config(tmp_path)
    assert config.get_value("general.framerate", path) is None


def test_set_replaces_active_line(tmp_path):
    path = make_config(tmp_path)
    config.set_value("general.bars", "40", path)
    assert config.get_value("general.bars", path) == "40"


def test_set_uncomments_line(tmp_path):
    path = make_config(tmp_path)
    config.set_value("color.gradient", "1", path)
    assert config.get_value("color.gradient", path) == "1"


def test_set_adds_key_to_existing_section(tmp_path):
    path = make_config(tmp_path)
    config.set_value("general.framerate", "60", path)
    assert config.get_value("general.framerate", path) == "60"


def test_set_adds_new_section(tmp_path):
    path = make_config(tmp_path)
    config.set_value("output.method", "noncurses", path)
    assert config.get_value("output.method", path) == "noncurses"


def test_comments_are_kept(tmp_path):
    path = make_config(tmp_path)
    config.set_value("general.bars", "40", path)
    assert "; bars = 0" in path.read_text(encoding="utf-8")


def test_list_settings(tmp_path):
    path = make_config(tmp_path)
    assert config.list_settings(path) == [("general.bars", "20")]


def test_backup_is_created_once(tmp_path):
    path = make_config(tmp_path)
    config.backup(path)
    config.set_value("general.bars", "40", path)
    config.backup(path)

    backup = tmp_path / "config.bak"
    assert "bars = 20" in backup.read_text(encoding="utf-8")
