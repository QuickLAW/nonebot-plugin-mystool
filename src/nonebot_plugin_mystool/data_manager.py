
import json
from typing import Optional
from pydantic import ValidationError
from nonebot.log import logger

from .config import DATA_PATH
from .model import PluginData

PLUGIN_DATA_PATH = DATA_PATH / "dataV2.json"

class PluginDataManager:
    plugin_data: PluginData = PluginData()

    @classmethod
    def load_plugin_data(cls):
        if PLUGIN_DATA_PATH.exists() and PLUGIN_DATA_PATH.is_file():
            try:
                with open(PLUGIN_DATA_PATH, "r", encoding="utf-8") as f:
                    plugin_data_dict = json.load(f)
                cls.plugin_data = PluginData.model_validate(plugin_data_dict)
            except (ValidationError, json.JSONDecodeError):
                logger.exception(f"Failed to load plugin data from {PLUGIN_DATA_PATH}")
                raise
            except Exception:
                logger.exception(f"Failed to read plugin data from {PLUGIN_DATA_PATH}")
                raise
        else:
            cls.plugin_data = PluginData()
            cls.write_plugin_data()
            logger.info(f"Created default plugin data at {PLUGIN_DATA_PATH}")

    @classmethod
    def write_plugin_data(cls):
        try:
            str_data = cls.plugin_data.model_dump_json(indent=4)
            PLUGIN_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(PLUGIN_DATA_PATH, "w", encoding="utf-8") as f:
                f.write(str_data)
            return True
        except Exception:
            logger.exception("Failed to write plugin data")
            return False

    @classmethod
    def do_user_bind(cls, src: str = None, dst: str = None, write: bool = False):
        if src is None or dst is None:
            # Sync all bindings
            for x, y in cls.plugin_data.user_bind.items():
                if y in cls.plugin_data.users:
                    cls.plugin_data.users[x] = cls.plugin_data.users[y]
                else:
                    logger.error(f"User bind failed: target user {y} does not exist")
        else:
            # Sync specific binding
            if dst in cls.plugin_data.users:
                cls.plugin_data.user_bind[src] = dst
                cls.plugin_data.users[src] = cls.plugin_data.users[dst]
                if write:
                    cls.write_plugin_data()
            else:
                logger.error(f"User bind failed: target user {dst} does not exist")

# Load data on import? Or explicit init?
# Explicit init is better for control, but for now let's follow pattern
PluginDataManager.load_plugin_data()
