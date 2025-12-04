
from typing import Dict, Optional, Any, Type
from pydantic import BaseModel
from ..utils import logger
from ..model import ApiResultHandler

IncorrectReturn = (KeyError, TypeError, AttributeError, IndexError, ValueError)

def is_incorrect_return(exception: Exception, *addition_exceptions: Type[Exception]) -> bool:
    exceptions = IncorrectReturn + addition_exceptions
    return isinstance(exception, exceptions) or isinstance(exception.__cause__, exceptions)
