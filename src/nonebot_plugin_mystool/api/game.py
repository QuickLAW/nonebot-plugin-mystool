
from typing import List, Optional, Tuple, Literal, Set, Type, Union
from urllib.parse import urlencode

import httpx
import tenacity

from ..consts import (
    HEADERS_API_TAKUMI_MOBILE, HEADERS_GENSHIN_STATUS_BBS, HEADERS_GENSHIN_STATUS_WIDGET,
    HEADERS_STARRAIL_STATUS_WIDGET, URL_GENSHEN_NOTE_BBS, URL_GENSHEN_NOTE_WIDGET,
    URL_STARRAIL_NOTE_WIDGET, URL_SIGN_REWARD, URL_SIGN_INFO, URL_SIGN_SIGN,
    HEADERS_SIGN_REWARD
)
from ..model import (
    GameRecord, BaseApiStatus, Award, GameSignInfo, GeetestResult, MmtData, UserAccount,
    GenshinNoteStatus, GenshinNote, StarRailNoteStatus, StarRailNote
)
from ..utils import logger, generate_ds, get_async_retry, generate_fp_locally
from ..config import plugin_config
from .base import ApiResultHandler, is_incorrect_return, IncorrectReturn
from .user import device_login, device_save, get_game_record, get_game_list

class BaseGameSign:
    name: str
    en_name: str
    act_id: str
    url_reward = URL_SIGN_REWARD
    url_info = URL_SIGN_INFO
    url_sign = URL_SIGN_SIGN
    headers_general = HEADERS_API_TAKUMI_MOBILE.copy()
    headers_reward = HEADERS_SIGN_REWARD.copy()
    game_id = int

    available_game_signs: Set[Type["BaseGameSign"]] = set()

    def __init__(self, account: UserAccount, records: List[GameRecord]):
        self.account = account
        self.record = next(filter(lambda x: x.game_id == self.game_id, records), None)
        reward_params = {
            "lang": "zh-cn",
            "act_id": self.act_id
        }
        self.url_reward = f"{self.url_reward}?{urlencode(reward_params)}"
        info_params = {
            "lang": "zh-cn",
            "act_id": self.act_id,
            "region": self.record.region if self.record else None,
            "uid": self.record.game_role_id if self.record else None
        }
        self.url_info = f"{self.url_info}?{urlencode(info_params)}"

    @property
    def has_record(self) -> bool:
        return self.record is not None

    async def get_rewards(self, retry: bool = True) -> Tuple[BaseApiStatus, Optional[List[Award]]]:
        try:
            async for attempt in get_async_retry(retry):
                with attempt:
                    async with httpx.AsyncClient() as client:
                        res = await client.get(self.url_reward, headers=self.headers_reward,
                                               timeout=plugin_config.preference.timeout)
                    award_list = []
                    for award in res.json()["data"]["awards"]:
                        award_list.append(Award.model_validate(award))
                    return BaseApiStatus(success=True), award_list
        except tenacity.RetryError as e:
            if is_incorrect_return(e):
                logger.exception(f"获取签到奖励信息 - 服务器没有正确返回")
                return BaseApiStatus(incorrect_return=True), None
            else:
                logger.exception(f"获取签到奖励信息 - 请求失败")
                return BaseApiStatus(network_error=True), None

    async def get_info(
            self,
            platform: Literal["ios", "android"] = "ios",
            retry: bool = True
    ) -> Tuple[BaseApiStatus, Optional[GameSignInfo]]:
        headers = self.headers_general.copy()
        headers["x-rpc-device_id"] = self.account.device_id_ios if platform == "ios" else self.account.device_id_android

        try:
            async for attempt in get_async_retry(retry):
                with attempt:
                    headers["DS"] = generate_ds() if platform == "ios" else generate_ds(platform="android")
                    async with httpx.AsyncClient() as client:
                        res = await client.get(self.url_info, headers=headers,
                                               cookies=self.account.cookies.dict(),
                                               timeout=plugin_config.preference.timeout)
                    api_result = ApiResultHandler(res.json())
                    if api_result.login_expired:
                        logger.info(
                            f"获取签到数据 - 用户 {self.account.display_name} 登录失效")
                        return BaseApiStatus(login_expired=True), None
                    if api_result.invalid_ds:
                        logger.info(
                            f"获取签到数据 - 用户 {self.account.display_name} DS 校验失败")
                        return BaseApiStatus(invalid_ds=True), None
                    return BaseApiStatus(success=True), GameSignInfo.model_validate(api_result.data)
        except tenacity.RetryError as e:
            if is_incorrect_return(e):
                logger.exception(f"获取签到数据 - 服务器没有正确返回")
                return BaseApiStatus(incorrect_return=True), None
            else:
                logger.exception(f"获取签到数据 - 请求失败")
                return BaseApiStatus(network_error=True), None

    async def sign(self,
                   platform: Literal["ios", "android"] = "ios",
                   mmt_data: MmtData = None,
                   geetest_result: GeetestResult = None,
                   retry: bool = True) -> Tuple[BaseApiStatus, Optional[MmtData]]:
        if not self.record:
            return BaseApiStatus(success=True), None
        content = {
            "act_id": self.act_id,
            "region": self.record.region,
            "uid": self.record.game_role_id
        }
        headers = self.headers_general.copy()
        if platform == "ios":
            headers["x-rpc-device_id"] = self.account.device_id_ios
            headers["Sec-Fetch-Dest"] = "empty"
            headers["Sec-Fetch-Site"] = "same-site"
            headers["DS"] = generate_ds()
        else:
            await device_login(self.account)
            await device_save(self.account)
            headers["x-rpc-device_id"] = self.account.device_id_android
            headers["x-rpc-device_model"] = plugin_config.device_config.X_RPC_DEVICE_MODEL_ANDROID
            headers["User-Agent"] = plugin_config.device_config.USER_AGENT_ANDROID
            headers["x-rpc-device_name"] = plugin_config.device_config.X_RPC_DEVICE_NAME_ANDROID
            headers["x-rpc-channel"] = plugin_config.device_config.X_RPC_CHANNEL_ANDROID
            headers["x-rpc-sys_version"] = plugin_config.device_config.X_RPC_SYS_VERSION_ANDROID
            headers["x-rpc-client_type"] = "2"
            headers["DS"] = generate_ds(data=content)
            headers.pop("x-rpc-platform", None)

        try:
            async for attempt in get_async_retry(retry):
                with attempt:
                    if geetest_result:
                        headers["x-rpc-validate"] = geetest_result.validate
                        headers["x-rpc-challenge"] = mmt_data.challenge
                        headers["x-rpc-seccode"] = geetest_result.seccode
                        logger.info("游戏签到 - 尝试使用人机验证结果进行签到")

                    async with httpx.AsyncClient() as client:
                        res = await client.post(
                            self.url_sign,
                            headers=headers,
                            cookies=self.account.cookies.dict(),
                            timeout=plugin_config.preference.timeout,
                            json=content
                        )

                    api_result = ApiResultHandler(res.json())
                    if api_result.login_expired:
                        logger.info(
                            f"游戏签到 - 用户 {self.account.display_name} 登录失效")
                        return BaseApiStatus(login_expired=True), None
                    elif api_result.invalid_ds:
                        logger.info(
                            f"游戏签到 - 用户 {self.account.display_name} DS 校验失败")
                        return BaseApiStatus(invalid_ds=True), None
                    elif api_result.data.get("risk_code") != 0:
                        logger.warning(
                            f"游戏签到 - 用户 {self.account.display_name} 可能被人机验证阻拦")
                        return BaseApiStatus(need_verify=True), MmtData.model_validate(api_result.data)
                    else:
                        logger.success(f"游戏签到 - 用户 {self.account.display_name} 签到成功")
                        return BaseApiStatus(success=True), None

        except tenacity.RetryError as e:
            if is_incorrect_return(e):
                logger.exception(f"游戏签到 - 服务器没有正确返回")
                return BaseApiStatus(incorrect_return=True), None
            else:
                logger.exception(f"游戏签到 - 请求失败")
                return BaseApiStatus(network_error=True), None

class GenshinImpactSign(BaseGameSign):
    name = "原神"
    en_name = "GenshinImpact"
    act_id = "e202311201442471"
    game_id = 2
    headers_general = BaseGameSign.headers_general.copy()
    headers_reward = BaseGameSign.headers_reward.copy()
    for headers in headers_general, headers_reward:
        headers["x-rpc-signgame"] = "hk4e"
        headers["Origin"] = "https://act.mihoyo.com"
        headers["Referer"] = "https://act.mihoyo.com/"

class HonkaiImpact3Sign(BaseGameSign):
    name = "崩坏3"
    en_name = "HonkaiImpact3"
    act_id = "e202306201626331"
    game_id = 1

class HoukaiGakuen2Sign(BaseGameSign):
    name = "崩坏学园2"
    en_name = "HoukaiGakuen2"
    act_id = "e202203291431091"
    game_id = 3

class TearsOfThemisSign(BaseGameSign):
    name = "未定事件簿"
    en_name = "TearsOfThemis"
    act_id = "e202202251749321"
    game_id = 4

class StarRailSign(BaseGameSign):
    name = "崩坏：星穹铁道"
    en_name = "StarRail"
    act_id = "e202304121516551"
    game_id = 6

class ZenlessZoneZeroSign(BaseGameSign):
    name = "绝区零"
    en_name = "ZenlessZoneZero"
    act_id = "e202406242138391"
    game_id = 8
    url_reward = "https://act-nap-api.mihoyo.com/event/luna/zzz/home"
    url_info = "https://act-nap-api.mihoyo.com/event/luna/zzz/info"
    url_sign = "https://act-nap-api.mihoyo.com/event/luna/zzz/sign"
    headers_general = BaseGameSign.headers_general.copy()
    headers_reward = BaseGameSign.headers_reward.copy()
    for headers in headers_general, headers_reward:
        headers["x-rpc-signgame"] = "zzz"
        headers["Origin"] = "https://act.mihoyo.com"
        headers["Referer"] = "https://act.mihoyo.com/"
        headers["Host"] = "act-nap-api.mihoyo.com"

BaseGameSign.available_game_signs.add(GenshinImpactSign)
BaseGameSign.available_game_signs.add(HonkaiImpact3Sign)
BaseGameSign.available_game_signs.add(HoukaiGakuen2Sign)
BaseGameSign.available_game_signs.add(TearsOfThemisSign)
BaseGameSign.available_game_signs.add(StarRailSign)
BaseGameSign.available_game_signs.add(ZenlessZoneZeroSign)

async def genshin_note(account: UserAccount) -> Tuple[
    Union[BaseApiStatus, GenshinNoteStatus],
    Optional[GenshinNote]
]:
    game_record_status, records = await get_game_record(account)
    if not game_record_status:
        return GenshinNoteStatus(game_record_failed=True), None
    game_list_status, game_list = await get_game_list()
    if not game_list_status:
        return GenshinNoteStatus(game_list_failed=True), None
    game_filter = filter(lambda x: x.en_name == 'ys', game_list)
    game_info = next(game_filter, None)
    if not game_info:
        return GenshinNoteStatus(no_genshin_account=True), None
    else:
        game_id = game_info.id
    flag = True
    for record in records:
        if record.game_id == game_id:
            try:
                flag = False
                params = {"role_id": record.game_role_id, "server": record.region}
                headers = HEADERS_GENSHIN_STATUS_BBS.copy()
                headers["x-rpc-device_id"] = account.device_id_android
                headers["x-rpc-device_fp"] = account.device_id_android or generate_fp_locally()
                async for attempt in get_async_retry(False):
                    with attempt:
                        headers["DS"] = generate_ds(
                            params={"role_id": record.game_role_id, "server": record.region})
                        async with httpx.AsyncClient() as client:
                            res = await client.get(
                                URL_GENSHEN_NOTE_BBS,
                                headers=headers,
                                cookies=account.cookies.dict(v2_stoken=True, cookie_type=True),
                                params=params,
                                timeout=plugin_config.preference.timeout
                            )
                        api_result = ApiResultHandler(res.json())
                        if api_result.login_expired:
                            logger.info(
                                f"原神实时便笺: 用户 {account.display_name} 登录失效")
                            return GenshinNoteStatus(login_expired=True), None

                        if api_result.invalid_ds:
                            logger.info(
                                f"原神实时便笺: 用户 {account.display_name} DS 校验失败")
                        if api_result.retcode == 1034:
                            logger.info(
                                f"原神实时便笺: 用户 {account.display_name} 可能被验证码阻拦")
                        if not api_result.success:
                            headers["DS"] = generate_ds()
                            headers["x-rpc-device_id"] = account.device_id_ios
                            async with httpx.AsyncClient() as client:
                                res = await client.get(
                                    URL_GENSHEN_NOTE_WIDGET,
                                    headers=headers,
                                    cookies=account.cookies.dict(v2_stoken=True, cookie_type=True),
                                    timeout=plugin_config.preference.timeout
                                )
                            api_result = ApiResultHandler(res.json())
                            return GenshinNoteStatus(success=True), \
                                GenshinNote.model_validate(api_result.data)
                        return GenshinNoteStatus(success=True), GenshinNote.model_validate(api_result.data)
            except tenacity.RetryError as e:
                if is_incorrect_return(e):
                    logger.exception(f"原神实时便笺: 服务器没有正确返回")
                    return GenshinNoteStatus(incorrect_return=True), None
                else:
                    logger.exception(f"原神实时便笺: 请求失败")
                    return GenshinNoteStatus(network_error=True), None
    if flag:
        return GenshinNoteStatus(no_genshin_account=True), None

async def starrail_note(account: UserAccount) -> Tuple[
    Union[BaseApiStatus, StarRailNoteStatus],
    Optional[StarRailNote]
]:
    game_record_status, records = await get_game_record(account)
    if not game_record_status:
        return StarRailNoteStatus(game_record_failed=True), None
    game_list_status, game_list = await get_game_list()
    if not game_list_status:
        return StarRailNoteStatus(game_list_failed=True), None
    game_filter = filter(lambda x: x.en_name == 'sr', game_list)
    game_info = next(game_filter, None)
    if not game_info:
        return StarRailNoteStatus(no_starrail_account=True), None
    else:
        game_id = game_info.id
    flag = True
    for record in records:
        if record.game_id == game_id:
            try:
                flag = False
                headers = HEADERS_STARRAIL_STATUS_WIDGET.copy()
                url = f"{URL_STARRAIL_NOTE_WIDGET}"
                async for attempt in get_async_retry(False):
                    with attempt:
                        headers["DS"] = generate_ds(data={})
                        async with httpx.AsyncClient() as client:
                            cookies = account.cookies.dict(v2_stoken=True, cookie_type=True)
                            res = await client.get(url, headers=headers,
                                                   cookies=cookies,
                                                   timeout=plugin_config.preference.timeout)
                        api_result = ApiResultHandler(res.json())
                        if api_result.login_expired:
                            logger.info(
                                f"崩铁实时便笺: 用户 {account.display_name} 登录失效")
                            return StarRailNoteStatus(login_expired=True), None

                        if api_result.invalid_ds:
                            logger.info(
                                f"崩铁实时便笺: 用户 {account.display_name} DS 校验失败")
                        if api_result.retcode == 1034:
                            logger.info(
                                f"崩铁实时便笺: 用户 {account.display_name} 可能被验证码阻拦")
                        return StarRailNoteStatus(success=True), StarRailNote.model_validate(api_result.data)
            except tenacity.RetryError as e:
                if is_incorrect_return(e):
                    logger.exception("崩铁实时便笺: 服务器没有正确返回")
                    return StarRailNoteStatus(incorrect_return=True), None
                else:
                    logger.exception("崩铁实时便笺: 请求失败")
                    return StarRailNoteStatus(network_error=True), None
    if flag:
        return StarRailNoteStatus(no_starrail_account=True), None
