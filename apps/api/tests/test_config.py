from pathlib import Path

import app.config as config


def test_env_file_lookup_is_safe_inside_container_layout(tmp_path, monkeypatch) -> None:
    # В образе код лежит в /app/app — там всего три родителя, индекс [3] не существует.
    fake_module = tmp_path / "app" / "config.py"
    fake_module.parent.mkdir()
    fake_module.write_text("")
    monkeypatch.setattr(config, "__file__", str(fake_module))
    monkeypatch.delenv("ENV_FILE", raising=False)
    monkeypatch.chdir(tmp_path)

    assert config._find_env_file() is None


def test_env_file_can_be_overridden(tmp_path, monkeypatch) -> None:
    env_file = tmp_path / "custom.env"
    env_file.write_text("")
    monkeypatch.setenv("ENV_FILE", str(env_file))

    assert config._find_env_file() == Path(env_file)
