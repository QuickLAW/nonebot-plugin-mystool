from typing import Optional, NamedTuple

from pydantic import BaseModel

from .base import BaseModelWithUpdate


class Good(BaseModelWithUpdate):
    """
    商品数据
    """
    type: int
    """为 1 时商品只有在指定时间开放兑换；为 0 时商品任何时间均可兑换"""
    next_time: Optional[int] = None
    """为 0 表示任何时间均可兑换或兑换已结束"""
    status: Optional[str] = None
    sale_start_time: Optional[int] = None
    time_by_detail: Optional[int] = None
    next_num: Optional[int] = None
    account_exchange_num: int
    """已经兑换次数"""
    account_cycle_limit: int
    """最多可兑换次数"""
    account_cycle_type: str
    """限购类型 Literal["forever", "month", "not_limit"]"""
    game_biz: Optional[str] = None
    """商品对应的游戏区服（如 hk4e_cn）（单独查询一个商品时）"""
    game: Optional[str] = None
    """商品对应的游戏"""
    unlimit: Optional[bool] = None
    """是否为不限量商品"""

    # 以下为实际会用到的属性

    name: Optional[str] = None
    """商品名称（单独查询一个商品时）"""
    goods_name: Optional[str] = None
    """商品名称（查询商品列表时）"""

    goods_id: str
    """商品ID(Good_ID)"""

    price: int
    """商品价格"""

    icon: str
    """商品图片链接"""

    def update(self, obj):
        return super().update(obj)

    @property
    def time(self):
        """
        兑换时间

        :return: 如果返回`None`，说明任何时间均可兑换或兑换已结束。
        """
        # "next_time" 为 0 表示任何时间均可兑换或兑换已结束
        if self.next_time == 0:
            return None
        # TODO: 暂时不知道为何 self.sale_start_time 是 str 类型而不是 int 类型
        sale_start_time = int(self.sale_start_time) if self.sale_start_time else 0
        import time
        if sale_start_time and time.time() < sale_start_time < self.next_time:
            return sale_start_time
        else:
            return self.next_time

    @property
    def time_text(self):
        """
        商品的兑换时间文本

        :return:
        如果返回`None`，说明需要进一步查询商品详细信息才能获取兑换时间
        """
        if self.time_end:
            return "已结束"
        elif self.time == 0:
            return None
        elif self.time_limited:
            from datetime import datetime
            import pytz
            from ..config import plugin_config
            if zone := plugin_config.preference.timezone:
                tz_info = pytz.timezone(zone)
                date_time = datetime.fromtimestamp(self.time, tz_info)
            else:
                date_time = datetime.fromtimestamp(self.time)
            return date_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return "任何时间"

    @property
    def stoke_text(self):
        """
        商品的库存文本
        """
        if self.time_end:
            return "无"
        elif self.time_limited:
            return str(self.num)
        else:
            return "不限"

    @property
    def time_limited(self):
        """
        是否为限时商品
        """
        # 不限量被认为是不限时商品
        return not self.unlimit

    @property
    def time_end(self):
        """
        兑换是否已经结束
        """
        return self.next_time == 0

    @property
    def num(self):
        """
        库存
        如果返回`None`，说明库存不限
        """
        if self.type != 1 and self.next_num == 0:
            return None
        else:
            return self.next_num

    @property
    def limit(self):
        """
        限购，返回元组 (已经兑换次数, 最多可兑换次数, 限购类型)
        """
        return (self.account_exchange_num,
                self.account_cycle_limit, self.account_cycle_type)

    @property
    def is_virtual(self):
        """
        是否为虚拟商品
        """
        return self.type == 2

    @property
    def general_name(self):
        return self.name or self.goods_name


class GameRecord(BaseModel):
    """
    用户游戏数据
    """
    region_name: str
    """服务器区名"""

    game_id: int
    """游戏ID"""

    level: int
    """用户游戏等级"""

    region: str
    """服务器区号"""

    game_role_id: str
    """用户游戏UID"""

    nickname: str
    """用户游戏昵称"""


class GameInfo(BaseModel):
    """
    游戏信息数据
    """
    id: int
    """游戏ID"""

    app_icon: str
    """游戏App图标链接(大)"""

    op_name: str
    """游戏代号(英文数字, 例如hk4e)"""

    en_name: str
    """游戏代号2(英文数字, 例如ys)"""

    icon: str
    """游戏图标链接(圆形, 小)"""

    name: str
    """游戏名称"""


class GameSignInfo(BaseModel):
    is_sign: bool
    """今日是否已经签到"""
    total_sign_day: int
    """已签多少天"""
    sign_cnt_missed: int
    """漏签多少天"""


class Award(BaseModel):
    """
    签到奖励数据
    """
    name: str
    """签到获得的物品名称"""
    icon: str
    """物品图片链接"""
    cnt: int
    """物品数量"""
