import sys
from unittest.mock import MagicMock

# Create mocks
mock_nonebot = MagicMock()
mock_driver = MagicMock()
mock_config = MagicMock()
mock_config.command_start = ["/"]  # Provide a default command start
mock_driver.config = mock_config
mock_nonebot.get_driver.return_value = mock_driver

# Mock require
def mock_require(name):
    return MagicMock()
mock_nonebot.require = mock_require

# Apply mocks
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

import pytest
from nonebot_plugin_mystool import consts
from nonebot_plugin_mystool.api import game

def test_consts_existence():
    """Test if new constants exist in consts.py"""
    assert hasattr(consts, 'HEADERS_API_TAKUMI_MOBILE')
    assert hasattr(consts, 'HEADERS_GENSHIN_STATUS_BBS')
    assert hasattr(consts, 'URL_GENSHEN_NOTE_BBS')
    assert hasattr(consts, 'URL_SIGN_REWARD')
    assert hasattr(consts, 'URL_SIGN_INFO')
    assert hasattr(consts, 'URL_SIGN_SIGN')
    assert hasattr(consts, 'HEADERS_SIGN_REWARD')

def test_game_module_imports():
    """Test if game module imports constants correctly"""
    assert game.HEADERS_API_TAKUMI_MOBILE == consts.HEADERS_API_TAKUMI_MOBILE
    assert game.URL_SIGN_REWARD == consts.URL_SIGN_REWARD

def test_base_game_sign_attributes():
    """Test if BaseGameSign uses the constants"""
    assert game.BaseGameSign.url_reward == consts.URL_SIGN_REWARD
    assert game.BaseGameSign.url_info == consts.URL_SIGN_INFO
    assert game.BaseGameSign.url_sign == consts.URL_SIGN_SIGN
    assert game.BaseGameSign.headers_reward == consts.HEADERS_SIGN_REWARD

def test_game_note_functions_exist():
    """Test if game note functions exist in api.game"""
    assert hasattr(game, 'genshin_note')
    assert hasattr(game, 'starrail_note')
