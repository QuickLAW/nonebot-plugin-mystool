from typing import Optional, List, Tuple, Union

import httpx
import tenacity
from pydantic import ValidationError

from ..consts import HEADERS_CHECK_GOOD, HEADERS_GOOD_LIST, URL_CHECK_GOOD, URL_GOOD_LIST
from ..model import Good, BaseApiStatus, GetGoodDetailStatus, ApiResultHandler
from ..utils import logger, get_async_retry, is_incorrect_return
from ..config import plugin_config

async def get_good_detail(good: Union[Good, str], retry: bool = True) -> Tuple[GetGoodDetailStatus, Optional[Good]]:
    """
    获取某商品的详细信息

    :param good: 商品对象 / 商品ID，如果指定为商品对象，则会更新商品对象的数据并返回其引用
    :param retry: 是否允许重试
    :return: 商品数据
    """
    good_id = good.goods_id if isinstance(good, Good) else good
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(URL_CHECK_GOOD.format(good_id), timeout=plugin_config.preference.timeout)
                api_result = ApiResultHandler(res.json())
                # -2109 商品不存在；-2105 商品已下架
                if api_result.retcode == -2109 or api_result.message == -2105:
                    return GetGoodDetailStatus(good_not_existed=True), None
                if isinstance(good, Good):
                    return GetGoodDetailStatus(success=True), good.update(api_result.data)
                else:
                    return GetGoodDetailStatus(success=True), Good.model_validate(api_result.data)
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception(f"米游币商品兑换 - 获取商品详细信息: 服务器没有正确返回")
            logger.debug(f"网络请求返回: {res.text}")
            return GetGoodDetailStatus(incorrect_return=True), None
        else:
            logger.exception(f"米游币商品兑换 - 获取商品详细信息: 网络请求失败")
            return GetGoodDetailStatus(network_error=True), None


async def get_good_games(retry: bool = True) -> Tuple[BaseApiStatus, Optional[List[Tuple[str, str]]]]:
    """
    获取商品分区列表

    :param retry: 是否允许重试
    :return: (商品分区全名, 字母简称) 的列表
    """
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(URL_GOOD_LIST.format(page=1,
                                                                game=""),
                                           headers=HEADERS_GOOD_LIST,
                                           timeout=plugin_config.preference.timeout)
                api_result = ApiResultHandler(res.json())
                return BaseApiStatus(success=True), list(map(lambda x: (x["name"], x["key"]), api_result.data["games"]))
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception(f"米游币商品兑换 - 获取商品列表: 服务器没有正确返回")
            logger.debug(f"网络请求返回: {res.text}")
            return BaseApiStatus(incorrect_return=True), None
        else:
            logger.exception("米游币商品兑换 - 获取商品列表: 网络请求失败")
            return BaseApiStatus(network_error=True), None


async def get_good_list(game: str = "", retry: bool = True) -> Tuple[
    BaseApiStatus,
    Optional[List[Good]]
]:
    """
    获取商品信息列表

    :param game: 游戏简称（默认为空，即获取所有游戏的商品）
    :param retry: 是否允许重试
    :return: 商品信息列表
    """
    good_list = []
    page = 1

    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(URL_GOOD_LIST.format(page=page,
                                                                game=game), headers=HEADERS_GOOD_LIST,
                                           timeout=plugin_config.preference.timeout)
                api_result = ApiResultHandler(res.json())
                goods_data = api_result.data["list"]
                goods = []
                for data in goods_data:
                    try:
                        goods.append(Good.model_validate(data))
                    except ValidationError as e:
                        logger.warning(f"获取商品列表 - 解析商品数据失败: {e}\n数据: {data}")
                        continue

                # 判断是否已经读完所有商品
                if not goods:
                    break
                else:
                    good_list += goods
                page += 1
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            logger.exception("获取商品信息列表 - 获取商品列表: 服务器没有正确返回")
            logger.debug(f"网络请求返回: {res.text}")
            return BaseApiStatus(incorrect_return=True), None
        else:
            logger.exception("获取商品信息列表 - 获取商品列表: 网络请求失败")
            return BaseApiStatus(network_error=True), None

    return BaseApiStatus(success=True), good_list
