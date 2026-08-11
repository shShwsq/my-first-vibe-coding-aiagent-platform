from typing import Any
import ast
import json
import logging
import pandas as pd

logger = logging.getLogger(__name__)


def convert_param_type(value: Any, param_type: str) -> Any:
    if value is None:
        return value
    
    if param_type == 'int':
        try:
            return int(value)
        except (ValueError, TypeError):
            return value
    elif param_type == 'float':
        try:
            return float(value)
        except (ValueError, TypeError):
            return value
    elif param_type == 'bool':
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return bool(value)
    elif param_type == 'list':
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return [item.strip() for item in value.split(',')]
        return [value]
    elif param_type == 'dict':
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                pass
        return value
    elif param_type == 'df':
        if isinstance(value, pd.DataFrame):
            return value
        if isinstance(value, dict):
            try:
                return pd.DataFrame(value)
            except Exception as e:
                logger.warning(f"无法将 dict 转换为 DataFrame: {e}")
                return value
        if isinstance(value, list):
            try:
                return pd.DataFrame(value)
            except Exception as e:
                logger.warning(f"无法将 list 转换为 DataFrame: {e}")
                return value
        if isinstance(value, str):
            # Try to parse as JSON
            try:
                data = json.loads(value)
                if isinstance(data, (dict, list)):
                    return pd.DataFrame(data)
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
            # If it's a string representation of a dict like "{'key': 'value'}"
            try:
                data = ast.literal_eval(value)
                if isinstance(data, (dict, list)):
                    return pd.DataFrame(data)
            except (ValueError, SyntaxError, MemoryError):
                pass
            logger.warning(f"无法将字符串转换为 DataFrame: {value[:100]}...")
            return value
        return value
    else:
        return str(value) if value is not None else value
