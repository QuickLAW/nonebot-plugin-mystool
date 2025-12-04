from typing import Optional, Dict, Any, Tuple, NamedTuple
import time
from datetime import datetime

from pydantic import BaseModel


class Address(BaseModel):
    """
    地址数据
    """
    connect_areacode: str
    """电话区号"""
    connect_mobile: str
    """电话号码"""

    # 以下为实际会用到的属性

    province_name: str
    """省"""

    city_name: str
    """市"""

    county_name: str
    """区/县"""

    addr_ext: str
    """详细地址"""

    connect_name: str
    """收货人姓名"""

    id: str
    """地址ID"""

    @property
    def phone(self) -> str:
        """
        联系电话(包含区号)
        """
        return self.connect_areacode + " " + self.connect_mobile


class MmtData(BaseModel):
    """
    短信验证码-人机验证任务申请-返回数据
    """
    challenge: Optional[str]
    gt: Optional[str]
    """验证ID，即 极验文档 中的captchaId，极验后台申请得到"""
    mmt_key: Optional[str]
    """验证任务"""
    new_captcha: Optional[bool]
    """宕机情况下使用"""
    risk_type: Optional[str]
    """结合风控融合，指定验证形式"""
    success: Optional[int]
    use_v4: Optional[bool]
    """是否使用极验第四代 GT4"""


class MissionData(BaseModel):
    points: int
    """任务米游币奖励"""
    name: str
    """任务名字，如 讨论区签到"""
    mission_key: str
    """任务代号，如 continuous_sign"""
    threshold: int
    """任务完成的最多次数"""


class MissionState(BaseModel):
    current_myb: int
    """用户当前米游币数量"""
    state_dict: Dict[str, Tuple[MissionData, int]]
    """所有任务对应的完成进度 {mission_key, (MissionData, 当前进度)}"""


class GenshinNote(BaseModel):
    """
    原神实时便笺数据 (从米游社内相关页面API的返回数据初始化)
    """
    current_resin: Optional[int] = None
    """当前树脂数量"""
    finished_task_num: Optional[int] = None
    """每日委托完成数"""
    current_expedition_num: Optional[int] = None
    """探索派遣 进行中的数量"""
    max_expedition_num: Optional[int] = None
    """探索派遣 最多派遣数"""
    current_home_coin: Optional[int] = None
    """洞天财瓮 未收取的宝钱数"""
    max_home_coin: Optional[int] = None
    """洞天财瓮 最多可容纳宝钱数"""
    transformer: Optional[Dict[str, Any]] = None
    """参量质变仪相关数据"""
    resin_recovery_time: Optional[int] = None
    """剩余树脂恢复时间"""

    @property
    def transformer_text(self):
        """
        参量质变仪状态文本
        """
        try:
            if not self.transformer['obtained']:
                return '未获得'
            elif self.transformer['recovery_time']['reached']:
                return '已准备就绪'
            else:
                return f"{self.transformer['recovery_time']['Day']} 天" \
                       f"{self.transformer['recovery_time']['Hour']} 小时 " \
                       f"{self.transformer['recovery_time']['Minute']} 分钟"
        except KeyError:
            return None

    @property
    def resin_recovery_text(self):
        """
        剩余树脂恢复文本
        """
        try:
            if not self.resin_recovery_time:
                return ':未获得时间数据'
            elif self.resin_recovery_time == 0:
                return '已准备就绪'
            else:
                recovery_timestamp = int(time.time()) + self.resin_recovery_time
                recovery_datetime = datetime.fromtimestamp(recovery_timestamp)
                return f"将在{recovery_datetime.strftime('%m-%d %H:%M')}回满"
        except KeyError:
            return None


class StarRailNote(BaseModel):
    """
    崩铁实时便笺数据 (从米游社内相关页面API的返回数据初始化)
    """
    current_stamina: Optional[int] = None
    """当前开拓力"""
    max_stamina: Optional[int] = None
    """最大开拓力"""
    stamina_recover_time: Optional[int] = None
    """剩余体力恢复时间"""
    current_train_score: Optional[int] = None
    """当前每日实训值"""
    max_train_score: Optional[int] = None
    """最大每日实训值"""
    current_rogue_score: Optional[int] = None
    """当前模拟宇宙积分"""
    max_rogue_score: Optional[int] = None
    """最大模拟宇宙积分"""
    accepted_expedition_num: Optional[int] = None
    """已接受委托数量"""
    total_expedition_num: Optional[int] = None
    """最大委托数量"""
    has_signed: Optional[bool] = None
    """当天是否签到"""

    @property
    def stamina_recover_text(self):
        """
        剩余体力恢复文本
        """
        try:
            if not self.stamina_recover_time:
                return ':未获得时间数据'
            elif self.stamina_recover_time == 0:
                return '已准备就绪'
            else:
                recovery_timestamp = int(time.time()) + self.stamina_recover_time
                recovery_datetime = datetime.fromtimestamp(recovery_timestamp)
                return f"将在{recovery_datetime.strftime('%m-%d %H:%M')}回满"
        except KeyError:
            return None


class GenshinNoteNotice(GenshinNote):
    """
    原神便笺通知状态
    """
    current_resin: bool = False
    """是否达到阈值"""
    current_resin_full: bool = False
    """是否溢出"""
    current_home_coin: bool = False
    transformer: bool = False


class StarRailNoteNotice(StarRailNote):
    """
    星穹铁道便笺通知状态
    """
    current_stamina: bool = False
    """是否达到阈值"""
    current_stamina_full: bool = False
    """是否溢出"""
    current_train_score: bool = False
    current_rogue_score: bool = False


GeetestResult = NamedTuple("GeetestResult", validate=str, seccode=str)
"""人机验证结果数据"""


class GeetestResultV4(BaseModel):
    """
    GEETEST GT4 人机验证结果数据
    """
    captcha_id: str
    lot_number: str
    pass_token: str
    gen_time: str
    captcha_output: str


class CommandUsage(BaseModel):
    """
    插件命令用法信息
    """
    name: Optional[str] = None
    description: Optional[str] = None
    usage: Optional[str] = None
