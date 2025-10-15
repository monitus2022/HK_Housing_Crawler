from typing import Union, Callable, List, Dict
from logger import housing_logger
import re
import pandas as pd

def flatten_dict(
    d: dict[str, dict], primary_key: str, sep: str = "_", 
    key_exclude: Union[str, list[str], Callable[[str], bool]] = None
) -> dict:
    """
    Flatten a nested dictionary, concatenating keys with a separator.
    Can exclude specific keys from the output by set of names or a callable function like lambda.
    Examples:
        # Exclude by list/str
        key_exclude=["id", "name"]
        
        # Exclude by callable - exclude keys containing "id"
        key_exclude=lambda key: "id" in key
    """
    if key_exclude is None:
        key_exclude = []

    if isinstance(key_exclude, str):
        key_exclude = [key_exclude]

    def should_exclude(key: str) -> bool:
        if callable(key_exclude):
            return key_exclude(key)
        else:
            return key in key_exclude

    items = {}
    for k, v in d.items():
        if should_exclude(k):
            continue
        elif isinstance(v, list) or isinstance(v, List):
            housing_logger.error(f"List found in flatten_dict for key {k}. Skipping.")
            raise ValueError("List found in flatten_dict, which is not supported.")
        elif not isinstance(v, dict) or not isinstance(v, Dict):
            final_key = f"{primary_key}{sep}{k}"
            items.update({final_key: v})
        else:
            nested_items = flatten_dict(
                v, primary_key=k, sep=sep, key_exclude=key_exclude)
            items.update(nested_items)

    return items

def keep_only_numbers(cell) -> any:
    """
    Turns a cell with mixed characters into a cell with only numbers.
    """
    if isinstance(cell, str):
        # Keep only numbers (remove all non-digit characters)
        numbers = re.sub(r"\D", "", cell)
        return numbers if numbers else pd.NA
    return cell

def convert_datetime(cell) -> any:
    """
    Converts a cell to datetime format.
    """
    if isinstance(cell, str):
        try:
            return pd.to_datetime(cell)
        except ValueError:
            return pd.NA
    return cell

def cookie_str_to_dict(cookie_str: str) -> dict[str, str]:
    """
    Convert a cookie string to a dictionary.
    Example input: "key1=value1; key2=value2; key3=value3"
    Example output: {"key1": "value1", "key2": "value2", "key3": "value3"}
    """
    cookies = {}
    for item in cookie_str.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            cookies[key.strip()] = value.strip()
    return cookies