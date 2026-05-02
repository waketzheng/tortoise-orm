"""
Tests for tortoise.config module - TortoiseConfig class.
"""

from pathlib import Path

import orjson
import pytest
import yaml

from tortoise.config import TortoiseConfig
from tortoise.exceptions import ConfigurationError


class TestTortoiseConfig:
    def test_from_invalid_dict(self):
        with pytest.raises(
            ConfigurationError, match="TortoiseConfig must be created from a mapping"
        ):
            TortoiseConfig.from_dict([])
        with pytest.raises(ConfigurationError, match='Config must define "connections" section'):
            TortoiseConfig.from_dict({})
        with pytest.raises(ConfigurationError, match='Config must define "apps" section'):
            TortoiseConfig.from_dict({"connections": ""})
        with pytest.raises(ConfigurationError, match='Config "connections" must be a mapping'):
            TortoiseConfig.from_dict({"connections": "", "apps": ""})
        with pytest.raises(ConfigurationError, match="Connection values must be mapping or string"):
            TortoiseConfig.from_dict({"connections": {"default": []}, "apps": ""})
        with pytest.raises(ConfigurationError, match="DBUrlConfig.url must be a non-empty string"):
            TortoiseConfig.from_dict({"connections": {"default": ""}, "apps": ""})
        with pytest.raises(ConfigurationError, match='Config "apps" must be a mapping'):
            TortoiseConfig.from_dict({"connections": {"default": "db.sqlite3"}, "apps": ""})
        with pytest.raises(ConfigurationError, match="App values must be mappings"):
            TortoiseConfig.from_dict(
                {"connections": {"default": "db.sqlite3"}, "apps": {"auth": ""}}
            )
        with pytest.raises(ConfigurationError, match='AppConfig requires "models"'):
            TortoiseConfig.from_dict(
                {"connections": {"default": "db.sqlite3"}, "apps": {"auth": {}}, "routers": {}}
            )
        with pytest.raises(
            ConfigurationError, match="AppConfig.models must be a non-empty list of strings"
        ):
            TortoiseConfig.from_dict(
                {
                    "connections": {"default": "db.sqlite3"},
                    "apps": {"auth": {"models": []}},
                    "routers": {},
                }
            )
        with pytest.raises(
            ConfigurationError, match="TortoiseConfig.routers must be a list or None"
        ):
            TortoiseConfig.from_dict(
                {
                    "connections": {"default": "db.sqlite3"},
                    "apps": {"auth": {"models": ["models"]}},
                    "routers": "",
                }
            )

    def test_from_dict(self):
        simple = {
            "connections": {"default": "sqlite://db.sqlite3"},
            "apps": {"app": {"models": ["app.models"]}},
        }
        assert TortoiseConfig.from_dict(simple) is not None
        full = {
            "connections": {
                "default": "sqlite://db.sqlite3",
                "second": "sqlite://db2.sqlite3",
            },
            "apps": {
                "app1": {"models": ["app1.models"]},
                "app2": {
                    "models": ["app2.models"],
                    "default_connection": "second",
                },
            },
            "routers": ["path.Router"],
            "use_tz": True,
            "timezone": "UTC",
        }
        assert TortoiseConfig.from_dict(full) is not None

    def test_from_config_file(self, tmp_path: Path):
        simple = {
            "connections": {"default": "sqlite://db.sqlite3"},
            "apps": {"app": {"models": ["app.models"]}},
        }
        file = tmp_path / "tortoise_conf.json"
        file.write_bytes(orjson.dumps(simple))
        filename: str = file.as_posix()
        assert (
            TortoiseConfig.from_config_file(file)
            == TortoiseConfig.from_config_file(filename)
            == TortoiseConfig.from_dict(simple)
            == TortoiseConfig.resolve_args(config_file=file)
        )

        yaml_file = file.with_suffix(".yml")
        with yaml_file.open("w") as f:
            yaml.safe_dump(dict(simple), f, default_flow_style=False)
        yaml_file_2 = file.with_suffix(".yaml")
        with yaml_file_2.open("w") as f2:
            yaml.safe_dump(simple, f2, default_flow_style=False)
        assert (
            TortoiseConfig.from_config_file(yaml_file)
            == TortoiseConfig.from_config_file(str(yaml_file))
            == TortoiseConfig.from_config_file(yaml_file_2)
            == TortoiseConfig.from_config_file(file)
            == TortoiseConfig.resolve_args(config_file=yaml_file)
        )

    def test_from_db_url_and_modules(self):
        simple = {
            "connections": {"default": "sqlite://db.sqlite3"},
            "apps": {
                "app": {
                    "models": ["app.models"],
                    "default_connection": "default",
                }
            },
        }
        db_url = simple["connections"]["default"]
        modules = {"app": simple["apps"]["app"]["models"]}
        typed_config = TortoiseConfig.from_db_url_and_modules(db_url, modules)
        assert typed_config == TortoiseConfig.resolve_args(db_url=db_url, modules=modules)
        assert typed_config.apps == TortoiseConfig.from_dict(simple).apps
