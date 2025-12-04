
from typing import Dict, Optional, Any, Type
from pydantic import BaseModel
from ..utils import logger

class ApiResultHandler(BaseModel):
    content: Dict[str, Any]
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    retcode: Optional[int] = None

    def __init__(self, content: Dict[str, Any]):
        super().__init__(content=content)
        self.data = self.content.get("data")
        
        for key in ["retcode", "status"]:
            if self.retcode is None:
                self.retcode = self.content.get(key)
                if self.retcode is None:
                    self.retcode = self.data.get(key) if self.data else None

        self.message: Optional[str] = None
        for key in ["message", "msg"]:
            if not self.message:
                self.message = self.content.get(key)
                if not self.message:
                    self.message = self.data.get(key) if self.data else None

    @property
    def success(self):
        return self.retcode == 1 or self.message in ["成功", "OK"] or self.retcode == 0

    @property
    def wrong_captcha(self):
        return self.retcode in [-201, -302] or self.message in ["验证码错误", "Captcha not match Err"]

    @property
    def login_expired(self):
        return self.retcode in [-100, 10001] or self.message in ["登录失效，请重新登录"]

    @property
    def invalid_ds(self):
        return self.message in ["invalid request"]

IncorrectReturn = (KeyError, TypeError, AttributeError, IndexError, ValueError)

def is_incorrect_return(exception: Exception, *addition_exceptions: Type[Exception]) -> bool:
    exceptions = IncorrectReturn + addition_exceptions
    return isinstance(exception, exceptions) or isinstance(exception.__cause__, exceptions)
