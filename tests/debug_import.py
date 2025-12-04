import sys
from unittest.mock import MagicMock
import os

# Mock nonebot and other dependencies
mock_nonebot = MagicMock()
mock_driver = MagicMock()
mock_config = MagicMock()
mock_config.command_start = ["/"]
mock_driver.config = mock_config
mock_nonebot.get_driver.return_value = mock_driver

def mock_require(name):
    return MagicMock()
mock_nonebot.require = mock_require

sys.modules["nonebot"] = mock_nonebot
sys.modules["nonebot.log"] = MagicMock()
sys.modules["nonebot.plugin"] = MagicMock()
sys.modules["nonebot.drivers"] = MagicMock()
sys.modules["nonebot_plugin_apscheduler"] = MagicMock()
sys.modules["nonebot_plugin_saa"] = MagicMock()

# Mock submodules recursively
sys.modules["nonebot.adapters"] = MagicMock()
sys.modules["nonebot.adapters.onebot"] = MagicMock()
sys.modules["nonebot.adapters.onebot.v11"] = MagicMock()
sys.modules["nonebot.adapters.qq"] = MagicMock()
sys.modules["nonebot.adapters.qq.exception"] = MagicMock()
sys.modules["nonebot.exception"] = MagicMock()
sys.modules["nonebot.internal"] = MagicMock()
sys.modules["nonebot.internal.matcher"] = MagicMock()
sys.modules["nonebot.internal.params"] = MagicMock()
sys.modules["nonebot.params"] = MagicMock()

# Add src to sys.path
sys.path.insert(0, os.path.join(os.getcwd(), "qqbot/sources/nonebot-plugin-mystool/src"))

try:
    # Try to import config directly from model
    import nonebot_plugin_mystool.model.config as model_config
    print("Imported model.config successfully")
    print("Has Preference:", hasattr(model_config, "Preference"))
    
    # Try to import model package
    import nonebot_plugin_mystool.model as model
    print("Imported model package successfully")
    print("Has Preference in model:", hasattr(model, "Preference"))

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
