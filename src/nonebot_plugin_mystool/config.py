
import os
import sys
from datetime import time, timedelta
from pathlib import Path
from typing import Union, Optional, Tuple, Dict, Any, Set

from nonebot import get_driver
from nonebot.log import logger
from pydantic import BaseModel, Field, field_validator

DATA_PATH = Path("data/nonebot-plugin-mystool").absolute()

class Preference(BaseModel):
    """
    Preference settings
    """
    github_proxy: Optional[str] = "https://mirror.ghproxy.com/"
    enable_connection_test: bool = True
    connection_test_interval: Optional[float] = 30
    timeout: float = 10
    max_retry_times: Optional[int] = 3
    retry_interval: float = 2
    timezone: Optional[str] = "Asia/Shanghai"
    exchange_thread_count: int = 2
    exchange_latency: Tuple[float, float] = (0, 0.5)
    exchange_duration: float = 5
    enable_log_output: bool = True
    log_head: str = ""
    log_path: Optional[Path] = DATA_PATH / "mystool.log"
    log_rotation: Union[str, int, time, timedelta] = "1 week"
    plugin_name: str = "nonebot_plugin_mystool"
    encoding: str = "utf-8"
    max_user: int = 0
    add_friend_accept: bool = True
    add_friend_welcome: bool = True
    command_start: str = ""
    sleep_time: float = 2
    plan_time: str = "00:30"
    resin_interval: int = 60
    global_geetest: bool = False
    geetest_url: Optional[str] = None
    geetest_params: Optional[Dict[str, Any]] = None
    geetest_json: Optional[Dict[str, Any]] = {
        "gt": "{gt}",
        "challenge": "{challenge}"
    }
    override_device_and_salt: bool = False
    enable_blacklist: bool = False
    blacklist_path: Optional[Path] = DATA_PATH / "blacklist.txt"
    enable_whitelist: bool = False
    whitelist_path: Optional[Path] = DATA_PATH / "whitelist.txt"
    enable_admin_list: bool = False
    admin_list_path: Optional[Path] = DATA_PATH / "admin_list.txt"
    game_token_app_id: str = "2"
    qrcode_query_interval: float = 1
    qrcode_wait_time: float = 120

    @field_validator("log_path")
    def check_log_path(cls, v: Optional[Path]):
        if v is None:
            return v
        absolute_path = v.absolute()
        if not os.path.exists(absolute_path) or not os.path.isfile(absolute_path):
            absolute_parent = absolute_path.parent
            try:
                os.makedirs(absolute_parent, exist_ok=True)
            except PermissionError:
                logger.warning(f"No permission to create log directory {absolute_parent}")
        elif not os.access(absolute_path, os.W_OK):
            logger.warning(f"No permission to write log file {absolute_path}")
        return v

class GoodListImageConfig(BaseModel):
    ICON_SIZE: Tuple[int, int] = (600, 600)
    WIDTH: int = 2000
    PADDING_ICON: int = 0
    PADDING_TEXT_AND_ICON_Y: int = 125
    PADDING_TEXT_AND_ICON_X: int = 10
    FONT_PATH: Union[Path, str, None] = None
    FONT_SIZE: int = 50
    SAVE_PATH: Path = DATA_PATH
    MULTI_PROCESS: bool = sys.platform != "win32"

class SaltConfig(BaseModel):
    SALT_IOS: str = "9ttJY72HxbjwWRNHJvn0n2AYue47nYsK"
    SALT_ANDROID: str = "BIPaooxbWZW02fGHZL1If26mYCljPgst"
    SALT_DATA: str = "t0qEgfub6cvueAPgR5m9aQWWVciEer7v"
    SALT_PARAMS: str = "xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs"
    SALT_PROD: str = "JwYDpKvLj6MrMqqYU6jTKF17KNO2PXoS"

class DeviceConfig(BaseModel):
    USER_AGENT_MOBILE: str = ("Mozilla/5.0 (iPhone; CPU iPhone OS 15_4 like Mac OS X) "
                              "AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.55.1")
    USER_AGENT_PC: str = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) "
                          "Version/16.0 Safari/605.1.15")
    USER_AGENT_OTHER: str = "Hyperion/275 CFNetwork/1402.0.8 Darwin/22.2.0"
    USER_AGENT_ANDROID: str = ("Mozilla/5.0 (Linux; Android 11; MI 8 SE Build/RQ3A.211001.001; wv) AppleWebKit/537.36 "
                               "(KHTML, like Gecko) Version/4.0 Chrome/104.0.5112.97 Mobile Safari/537.36 "
                               "miHoYoBBS/2.55.1")
    USER_AGENT_ANDROID_OTHER: str = "okhttp/4.9.3"
    USER_AGENT_WIDGET: str = "WidgetExtension/231 CFNetwork/1390 Darwin/22.0.0"

    X_RPC_DEVICE_MODEL_PC: str = "OS X 10.15.7"
    X_RPC_DEVICE_NAME_PC: str = "Microsoft Edge 103.0.1264.62"
    X_RPC_CLIENT_TYPE_PC: str = "4"
    X_RPC_DEVICE_MODEL_MOBILE: str = "iPhone10,2"
    X_RPC_DEVICE_NAME_MOBILE: str = "iPhone"
    X_RPC_APP_VERSION: str = "2.55.1"
    X_RPC_SYS_VERSION: str = "15.4.1"
    X_RPC_CHANNEL: str = "appstore"
    X_RPC_PLATFORM: str = "ios"

    X_RPC_DEVICE_MODEL_ANDROID: str = "MI 8 SE"
    X_RPC_DEVICE_NAME_ANDROID: str = "Xiaomi MI 8 SE"
    X_RPC_SYS_VERSION_ANDROID: str = "11"
    X_RPC_CHANNEL_ANDROID: str = "miyoushe"

    UA: str = '"Microsoft Edge";v="103", "Chromium";v="103", "Not;A=Brand";v="24"'
    UA_PLATFORM: str = '"macOS"'

class PluginConfig(BaseModel):
    preference: Preference = Preference()
    good_list_image_config: GoodListImageConfig = GoodListImageConfig()
    salt_config: SaltConfig = SaltConfig()
    device_config: DeviceConfig = DeviceConfig()

    def save_to_file(self, path: Path = DATA_PATH / "configV2.json"):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=4))

    @classmethod
    def load_from_file(cls, path: Path = DATA_PATH / "configV2.json") -> "PluginConfig":
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return cls.model_validate_json(f.read())
            except Exception as e:
                logger.error(f"Failed to load config from {path}: {e}")
        return cls()

# Global Config Instance
plugin_config = PluginConfig.load_from_file()
