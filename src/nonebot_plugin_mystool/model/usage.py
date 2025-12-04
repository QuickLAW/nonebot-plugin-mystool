from typing import Optional
from pydantic import BaseModel

class CommandUsage(BaseModel):
    """
    插件命令用法信息
    """
    name: Optional[str] = None
    description: Optional[str] = None
    usage: Optional[str] = None
