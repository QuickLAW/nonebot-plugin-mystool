
import time
from typing import Tuple, Optional, List, Union

import httpx
import tenacity

from ..consts import (
    HEADERS_GAME_RECORD, HEADERS_BBS_API, HEADERS_MYB, HEADERS_DEVICE, HEADERS_ADDRESS,
    URL_GAME_RECORD, URL_GAME_LIST, URL_MYB, URL_DEVICE_LOGIN, URL_DEVICE_SAVE,
    URL_ADDRESS, URL_GET_DEVICE_FP
)
from ..model import (
    BaseApiStatus, GameRecord, GameInfo, UserAccount, Address, GetFpStatus
)
from ..utils import (
    logger, get_async_retry, generate_ds, generate_device_id, generate_seed_id, generate_fp_locally
)
from ..config import plugin_config
from .base import ApiResultHandler, is_incorrect_return, IncorrectReturn

async def get_game_record(account: UserAccount, retry: bool = True) -> Tuple[BaseApiStatus, Optional[List[GameRecord]]]:
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(URL_GAME_RECORD.format(account.bbs_uid), headers=HEADERS_GAME_RECORD,
                                           cookies=account.cookies.dict(v2_stoken=True, cookie_type=True),
                                           timeout=plugin_config.preference.timeout)
                api_result = ApiResultHandler(res.json())
                if api_result.login_expired:
                    logger.info(
                        f"获取用户游戏数据(GameRecord) - 用户 {account.display_name} 登录失效")
                    return BaseApiStatus(login_expired=True), None
                return BaseApiStatus(success=True), list(
                    map(GameRecord.model_validate, api_result.data["list"]))
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception("获取用户游戏数据(GameRecord) - 服务器没有正确返回")
            return BaseApiStatus(incorrect_return=True), None
        else:
            logger.exception("获取用户游戏数据(GameRecord) - 请求失败")
            return BaseApiStatus(network_error=True), None

async def get_game_list(retry: bool = True) -> Tuple[BaseApiStatus, Optional[List[GameInfo]]]:
    headers = HEADERS_BBS_API.copy()
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                headers["DS"] = generate_ds()
                async with httpx.AsyncClient() as client:
                    res = await client.get(URL_GAME_LIST, headers=headers, timeout=plugin_config.preference.timeout)
                api_result = ApiResultHandler(res.json())
                return BaseApiStatus(success=True), list(
                    map(GameInfo.model_validate, api_result.data["list"]))
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception("获取游戏信息(GameInfo) - 服务器没有正确返回")
            return BaseApiStatus(incorrect_return=True), None
        else:
            logger.exception(f"获取游戏信息(GameInfo) - 请求失败")
            return BaseApiStatus(network_error=True), None

async def get_user_myb(account: UserAccount, retry: bool = True) -> Tuple[BaseApiStatus, Optional[int]]:
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(URL_MYB, headers=HEADERS_MYB,
                                           cookies=account.cookies.dict(v2_stoken=True, cookie_type=True),
                                           timeout=plugin_config.preference.timeout)
                api_result = ApiResultHandler(res.json())
                if api_result.login_expired:
                    logger.info(
                        f"获取用户米游币 - 用户 {account.display_name} 登录失效")
                    return BaseApiStatus(login_expired=True), None
                return BaseApiStatus(success=True), int(api_result.data["points"])
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception(f"获取用户米游币 - 服务器没有正确返回")
            return BaseApiStatus(incorrect_return=True), None
        else:
            logger.exception(f"获取用户米游币 - 请求失败")
            return BaseApiStatus(network_error=True), None

async def device_login(account: UserAccount, retry: bool = True):
    data = {
        "app_version": plugin_config.device_config.X_RPC_APP_VERSION,
        "device_id": account.device_id_android,
        "device_name": plugin_config.device_config.X_RPC_DEVICE_NAME_ANDROID,
        "os_version": "30",
        "platform": "Android",
        "registration_id": "1a0018970a5c00e814d"
    }
    headers = HEADERS_DEVICE.copy()
    headers["x-rpc-device_id"] = account.device_id_android
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                headers["DS"] = generate_ds(data)
                async with httpx.AsyncClient() as client:
                    res = await client.post(URL_DEVICE_LOGIN, headers=headers, json=data,
                                            cookies=account.cookies.dict(v2_stoken=True, cookie_type=True),
                                            timeout=plugin_config.preference.timeout)
                api_result = ApiResultHandler(res.json())
                if api_result.login_expired:
                    logger.info(
                        f"设备登录(device_login) - 用户 {account.display_name} 登录失效")
                    return BaseApiStatus(login_expired=True)
                if res.json()["message"] != "OK":
                    raise ValueError
                else:
                    return BaseApiStatus(success=True)
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception(f"设备登录(device_login) - 服务器没有正确返回")
            return BaseApiStatus(incorrect_return=True)
        else:
            logger.exception(f"设备登录(device_login) - 请求失败")
            return BaseApiStatus(network_error=True)

async def device_save(account: UserAccount, retry: bool = True):
    data = {
        "app_version": plugin_config.device_config.X_RPC_APP_VERSION,
        "device_id": account.device_id_android,
        "device_name": plugin_config.device_config.X_RPC_DEVICE_NAME_ANDROID,
        "os_version": "30",
        "platform": "Android",
        "registration_id": "1a0018970a5c00e814d"
    }
    headers = HEADERS_DEVICE.copy()
    headers["x-rpc-device_id"] = account.device_id_android
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                headers["DS"] = generate_ds(data)
                async with httpx.AsyncClient() as client:
                    res = await client.post(URL_DEVICE_SAVE, headers=headers, json=data,
                                            cookies=account.cookies.dict(v2_stoken=True, cookie_type=True),
                                            timeout=plugin_config.preference.timeout)
                api_result = ApiResultHandler(res.json())
                if api_result.login_expired:
                    logger.info(
                        f"设备保存(device_save) - 用户 {account.display_name} 登录失效")
                    return BaseApiStatus(login_expired=True)
                if res.json()["message"] != "OK":
                    raise ValueError
                else:
                    return BaseApiStatus(success=True)
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception(f"设备保存(device_save) - 服务器没有正确返回")
            return BaseApiStatus(incorrect_return=True)
        else:
            logger.exception(f"设备保存(device_save) - 请求失败")
            return BaseApiStatus(network_error=True)

async def get_address(account: UserAccount, retry: bool = True) -> Tuple[BaseApiStatus, Optional[List[Address]]]:
    headers = HEADERS_ADDRESS.copy()
    headers["x-rpc-device_id"] = account.device_id_ios
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(URL_ADDRESS.format(
                        round(time.time() * 1000)), headers=headers,
                        cookies=account.cookies.dict(v2_stoken=True, cookie_type=True),
                        timeout=plugin_config.preference.timeout)
                    api_result = ApiResultHandler(res.json())
                    if api_result.login_expired:
                        logger.info(
                            f"获取地址数据 - 用户 {account.display_name} 登录失效")
                        return BaseApiStatus(login_expired=True), None
                address_list = list(map(Address.model_validate, api_result.data["list"]))
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception("获取地址数据 - 服务器没有正确返回")
            return BaseApiStatus(incorrect_return=True), None
        else:
            logger.exception("获取地址数据 - 请求失败")
            return BaseApiStatus(network_error=True), None
    return BaseApiStatus(success=True), address_list

async def get_device_fp(device_id: str, retry: bool = True) -> Tuple[GetFpStatus, Optional[str]]:
    content = {
        "seed_id": generate_seed_id(),
        "device_id": device_id.lower(),
        "platform": "5",
        "seed_time": str(int(time.time() * 1000)),
        "ext_fields": "{\"userAgent\":\"Mozilla/5.0 (iPhone; CPU iPhone OS 16_2 like Mac OS X) AppleWebKit/605.1.15 "
                      f"(KHTML, like Gecko) miHoYoBBS/{plugin_config.device_config.X_RPC_APP_VERSION}\",\"browserScreenSize"
                      "\":243750,\"maxTouchPoints\":5,"
                      "\"isTouchSupported\":true,\"browserLanguage\":\"zh-CN\",\"browserPlat\":\"iPhone\","
                      "\"browserTimeZone\":\"Asia/Shanghai\",\"webGlRender\":\"Apple GPU\",\"webGlVendor\":\"Apple "
                      "Inc.\",\"numOfPlugins\":0,\"listOfPlugins\":\"unknown\",\"screenRatio\":3,"
                      "\"deviceMemory\":\"unknown\",\"hardwareConcurrency\":\"4\",\"cpuClass\":\"unknown\","
                      "\"ifNotTrack\":\"unknown\",\"ifAdBlock\":0,\"hasLiedResolution\":1,\"hasLiedOs\":0,"
                      "\"hasLiedBrowser\":0}",
        "app_name": "account_cn",
        "device_fp": generate_fp_locally()
    }
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.post(
                        URL_GET_DEVICE_FP,
                        json=content,
                        timeout=plugin_config.preference.timeout
                    )
                api_result = ApiResultHandler(res.json())
                if api_result.data["code"] == 403 or api_result.data["msg"] == "传入的参数有误":
                    logger.error("传入的参数有误")
                    return GetFpStatus(invalid_arguments=True), None
                elif api_result.success:
                    device_fp = api_result.data["device_fp"]
                    if not device_fp:
                        logger.error("获取 x-rpc-device_fp: 服务器返回的 device_fp 为空")
                        return GetFpStatus(incorrect_return=True), None
                    return GetFpStatus(success=True), device_fp

    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception("获取 x-rpc-device_fp: 服务器没有正确返回")
            return GetFpStatus(incorrect_return=True), None
        else:
            logger.exception("获取 x-rpc-device_fp: 网络请求失败")
            return GetFpStatus(network_error=True), None
