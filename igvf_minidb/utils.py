import logging
import re


logger = logging.getLogger(__name__)


def is_snake_case(s):
    pattern = r"^[a-z][a-z0-9]+(_[a-z0-9]+)*$"

    if re.match(pattern, s):
        return True
    else:
        return False


def is_upper_camel_case(s, strict=True):
    if strict:
        pattern = r"^([A-Z][a-z]+)+$"
    else:
        pattern = r"^([A-Z][A-Za-z]+)+$"

    if re.match(pattern, s):
        return True
    else:
        return False


def to_snake_case(s):
    """
    Convert CamelCase to snake_case.
    """
    if is_snake_case(s):
        return s

    elif is_upper_camel_case(s):
        return re.sub(r'(?<!^)(?=[A-Z])', '_', s).lower()

    raise ValueError("String to be converted should be snake_case or CamelCase.")


def to_upper_camel_case(s):
    """
    Convert either snake_case to CamelCase.
    """
    if is_upper_camel_case(s):
        return s

    elif is_snake_case(s):
        return "".join(x.capitalize() for x in s.lower().split("_"))

    raise ValueError("String should be snake_case or CamelCase.")
