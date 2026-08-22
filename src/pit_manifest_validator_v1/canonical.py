"""pit_canonical_json_v1 parse, typed-preprocessing, and RFC 8785 JCS helpers."""

from __future__ import annotations

from calendar import isleap
import hashlib
import json
import re
import unicodedata
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone


CANONICALIZATION_ID = "pit_canonical_json_v1"
IJSON_INT_MIN = -(2**53) + 1
IJSON_INT_MAX = (2**53) - 1
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SAFE_PUBLIC_ID_RE = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?$")
SAFE_FIELD_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SAFE_LOCATOR_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\[\]]{0,127}$")
DECIMAL_RE = re.compile(r"^-?(0|[1-9][0-9]*)(\.[0-9]*[1-9])?$")
DATE_RE = re.compile(r"^([0-9]{4})-([0-9]{2})-([0-9]{2})$")
TIMESTAMP_RE = re.compile(
    r"^([0-9]{4})-([0-9]{2})-([0-9]{2})"
    r"T([0-9]{2}):([0-9]{2}):([0-9]{2})"
    r"(?:\.([0-9]+))?"
    r"(Z|[+-][0-9]{2}:[0-9]{2})$"
)
_CONTROL_ESCAPES = {
    0x08: "\\b",
    0x09: "\\t",
    0x0A: "\\n",
    0x0C: "\\f",
    0x0D: "\\r",
}
_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


class ValidationError(ValueError):
    """Fail-closed validation error with a safe locator only."""

    def __init__(
        self,
        code: str,
        field: str,
        *,
        input_id: str | None = None,
        locator: str | None = None,
    ) -> None:
        self.code = code
        self.field = _safe_reported_name(field, fallback="field")
        self.input_id = _safe_reported_input_id(input_id)
        self.locator = _safe_reported_locator(locator)
        parts = [self.code]
        if self.input_id is not None:
            parts.append(f"input_id={self.input_id}")
        parts.append(f"field={self.field}")
        if self.locator is not None:
            parts.append(f"locator={self.locator}")
        super().__init__(" ".join(parts))


def _safe_reported_name(value: str, *, fallback: str) -> str:
    if SAFE_FIELD_RE.fullmatch(value):
        return value
    return fallback


def _safe_reported_input_id(value: str | None) -> str | None:
    if value is None:
        return None
    if SAFE_PUBLIC_ID_RE.fullmatch(value):
        return value
    return "unsafe"


def _safe_reported_locator(value: str | None) -> str | None:
    if value is None:
        return None
    if SAFE_LOCATOR_RE.fullmatch(value):
        return value
    return "locator"


def fail(
    code: str,
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> None:
    raise ValidationError(code, field, input_id=input_id, locator=locator)


def utf16_sort_key(value: str) -> bytes:
    return value.encode("utf-16-be")


def has_lone_surrogate(value: str) -> bool:
    return any(0xD800 <= ord(char) <= 0xDFFF for char in value)


def require_nfc(value: str, field: str, *, input_id: str | None = None, locator: str | None = None) -> str:
    if has_lone_surrogate(value):
        fail("LONE_SURROGATE", field, input_id=input_id, locator=locator)
    normalized = unicodedata.normalize("NFC", value)
    if normalized != value:
        fail("NOT_NFC", field, input_id=input_id, locator=locator)
    return value


def nfc_text(value: str, field: str, *, input_id: str | None = None, locator: str | None = None) -> str:
    if has_lone_surrogate(value):
        fail("LONE_SURROGATE", field, input_id=input_id, locator=locator)
    return unicodedata.normalize("NFC", value)


def is_sha256(value: object) -> bool:
    return isinstance(value, str) and SHA256_RE.fullmatch(value) is not None


def is_git_or_sha256(value: object) -> bool:
    return isinstance(value, str) and (
        SHA256_RE.fullmatch(value) is not None or GIT_SHA_RE.fullmatch(value) is not None
    )


def is_safe_public_id(value: object) -> bool:
    return isinstance(value, str) and SAFE_PUBLIC_ID_RE.fullmatch(value) is not None


def is_decimal_string(value: object) -> bool:
    if not isinstance(value, str) or DECIMAL_RE.fullmatch(value) is None:
        return False
    return value not in {"-0"}


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _object_without_duplicate_keys(
    pairs: Sequence[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            fail("DUPLICATE_KEY", "object")
        if not isinstance(key, str):
            fail("INVALID_KEY", "object")
        if has_lone_surrogate(key):
            fail("LONE_SURROGATE", "object")
        result[key] = value
    return result


def _parse_safe_integer(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError:
        fail("NON_IJSON_INTEGER", "number")
    if not (IJSON_INT_MIN <= parsed <= IJSON_INT_MAX):
        fail("NON_IJSON_INTEGER", "number")
    return parsed


def _reject_float(_: str) -> float:
    fail("RAW_FLOAT", "number")
    raise AssertionError("unreachable")


def _reject_constant(_: str) -> float:
    fail("NON_FINITE_NUMBER", "number")
    raise AssertionError("unreachable")


def parse_json_bytes(raw: bytes) -> object:
    """Parse UTF-8 JSON, rejecting duplicates, floats, and non-I-JSON integers."""
    if not isinstance(raw, bytes):
        fail("INVALID_JSON", "document")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        fail("INVALID_UTF8", "document")
    try:
        parsed = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
            parse_int=_parse_safe_integer,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except ValidationError:
        raise
    except json.JSONDecodeError:
        fail("INVALID_JSON", "document")
    _reject_surrogates(parsed, field="document")
    return parsed


def _reject_surrogates(value: object, *, field: str) -> None:
    if isinstance(value, str):
        if has_lone_surrogate(value):
            fail("LONE_SURROGATE", field)
        return
    if isinstance(value, list):
        for item in value:
            _reject_surrogates(item, field=field)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or has_lone_surrogate(key):
                fail("LONE_SURROGATE", field)
            _reject_surrogates(item, field=field)


def require_mapping(
    value: object,
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        fail("NOT_OBJECT", field, input_id=input_id, locator=locator)
    return value


def require_list(
    value: object,
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> list[object]:
    if not isinstance(value, list):
        fail("NOT_ARRAY", field, input_id=input_id, locator=locator)
    return value


def require_exact_keys(
    value: object,
    expected: set[str],
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> dict[str, object]:
    mapping = require_mapping(value, field, input_id=input_id, locator=locator)
    actual = set(mapping)
    if actual == expected:
        return mapping
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if unknown:
        safe_unknown = next((key for key in unknown if SAFE_FIELD_RE.fullmatch(key)), None)
        fail(
            "UNKNOWN_KEY",
            field,
            input_id=input_id,
            locator=(
                f"unknown.{safe_unknown}"
                if safe_unknown is not None
                else "unknown_key"
            ),
        )
    fail(
        "MISSING_KEY",
        field,
        input_id=input_id,
        locator=f"missing.{missing[0]}" if missing else locator,
    )
    raise AssertionError("unreachable")


def require_string(
    value: object,
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> str:
    if not isinstance(value, str):
        fail("NOT_STRING", field, input_id=input_id, locator=locator)
    if has_lone_surrogate(value):
        fail("LONE_SURROGATE", field, input_id=input_id, locator=locator)
    return value


def require_nonempty_nfc(
    value: object,
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> str:
    text = require_string(value, field, input_id=input_id, locator=locator)
    if not text:
        fail("EMPTY_STRING", field, input_id=input_id, locator=locator)
    if text == "UNKNOWN":
        fail("UNKNOWN_BLOCKED", field, input_id=input_id, locator=locator)
    return require_nfc(text, field, input_id=input_id, locator=locator)


def require_safe_public_id(
    value: object,
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> str:
    text = require_string(value, field, input_id=input_id, locator=locator)
    if not is_safe_public_id(text):
        fail("SAFE_PUBLIC_ID", field, input_id=input_id, locator=locator)
    return text


def require_sha256(
    value: object,
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> str:
    text = require_string(value, field, input_id=input_id, locator=locator)
    if not is_sha256(text):
        fail("NOT_SHA256", field, input_id=input_id, locator=locator)
    return text


def require_code_sha(
    value: object,
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> str:
    text = require_string(value, field, input_id=input_id, locator=locator)
    if not is_git_or_sha256(text):
        fail("NOT_CODE_SHA", field, input_id=input_id, locator=locator)
    return text


def require_bool(
    value: object,
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> bool:
    if not isinstance(value, bool):
        fail("NOT_BOOLEAN", field, input_id=input_id, locator=locator)
    return value


def require_nonnegative_int(
    value: object,
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        fail("NOT_INTEGER", field, input_id=input_id, locator=locator)
    if value < 0 or value > IJSON_INT_MAX:
        fail("NON_IJSON_INTEGER", field, input_id=input_id, locator=locator)
    return value


def require_literal(
    value: object,
    expected: str,
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> str:
    text = require_string(value, field, input_id=input_id, locator=locator)
    if text != expected:
        fail("UNEXPECTED_VALUE", field, input_id=input_id, locator=locator)
    return text


def require_enum(
    value: object,
    allowed: set[str],
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> str:
    text = require_string(value, field, input_id=input_id, locator=locator)
    if text == "UNKNOWN":
        fail("UNKNOWN_BLOCKED", field, input_id=input_id, locator=locator)
    if text not in allowed:
        fail("UNEXPECTED_VALUE", field, input_id=input_id, locator=locator)
    return text


def require_decimal_string(
    value: object,
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> str:
    text = require_string(value, field, input_id=input_id, locator=locator)
    if not is_decimal_string(text):
        fail("NOT_DECIMAL", field, input_id=input_id, locator=locator)
    return text


def _days_in_month(year: int, month: int) -> int:
    if month == 2 and isleap(year):
        return 29
    return _DAYS_IN_MONTH[month - 1]


def _validate_gregorian_date(
    year: int,
    month: int,
    day: int,
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> None:
    if year >= 9999:
        fail("SENTINEL_TIMESTAMP", field, input_id=input_id, locator=locator)
    if year < 1 or not 1 <= month <= 12:
        fail("INVALID_TIMESTAMP", field, input_id=input_id, locator=locator)
    if not 1 <= day <= _days_in_month(year, month):
        fail("INVALID_TIMESTAMP", field, input_id=input_id, locator=locator)


def require_date(
    value: object,
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> str:
    text = require_string(value, field, input_id=input_id, locator=locator)
    match = DATE_RE.fullmatch(text)
    if match is None:
        fail("INVALID_DATE", field, input_id=input_id, locator=locator)
    year, month, day = map(int, match.groups())
    _validate_gregorian_date(year, month, day, field, input_id=input_id, locator=locator)
    return text


def normalize_timestamp(
    value: object,
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> str:
    text = require_string(value, field, input_id=input_id, locator=locator)
    match = TIMESTAMP_RE.fullmatch(text)
    if match is None:
        fail("INVALID_TIMESTAMP", field, input_id=input_id, locator=locator)
    year, month, day, hour, minute, second = map(int, match.groups()[:6])
    fraction = match.group(7)
    zone = match.group(8)
    _validate_gregorian_date(year, month, day, field, input_id=input_id, locator=locator)
    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        fail("INVALID_TIMESTAMP", field, input_id=input_id, locator=locator)
    if zone != "Z":
        offset_hours = int(zone[1:3])
        offset_minutes = int(zone[4:6])
        if offset_hours > 23 or offset_minutes > 59:
            fail("INVALID_TIMESTAMP", field, input_id=input_id, locator=locator)
        try:
            local = datetime(
                year,
                month,
                day,
                hour,
                minute,
                second,
                tzinfo=timezone(
                    timedelta(
                        hours=offset_hours if zone[0] == "+" else -offset_hours,
                        minutes=offset_minutes if zone[0] == "+" else -offset_minutes,
                    )
                ),
            )
        except ValueError:
            fail("INVALID_TIMESTAMP", field, input_id=input_id, locator=locator)
        utc = local.astimezone(timezone.utc)
        year, month, day = utc.year, utc.month, utc.day
        hour, minute, second = utc.hour, utc.minute, utc.second
    if fraction is not None:
        fraction = fraction.rstrip("0")
    if not fraction:
        return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}Z"
    return (
        f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}"
        f".{fraction}Z"
    )


def require_nullable_timestamp(
    value: object,
    field: str,
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> str | None:
    if value is None:
        return None
    return normalize_timestamp(value, field, input_id=input_id, locator=locator)


def require_effective_interval(
    payload: Mapping[str, object],
    *,
    input_id: str | None = None,
    locator: str | None = None,
) -> tuple[str, str, str | None]:
    effective_from = normalize_timestamp(
        payload["effective_from"],
        "effective_from",
        input_id=input_id,
        locator=locator,
    )
    state = require_enum(
        payload["effective_to_state"],
        {"FINITE", "OPEN_IN_VINTAGE"},
        "effective_to_state",
        input_id=input_id,
        locator=locator,
    )
    raw_to = payload["effective_to"]
    if state == "FINITE":
        if raw_to is None:
            fail("TYPED_NULL", "effective_to", input_id=input_id, locator=locator)
        effective_to = normalize_timestamp(
            raw_to,
            "effective_to",
            input_id=input_id,
            locator=locator,
        )
    elif raw_to is not None:
        fail("TYPED_NULL", "effective_to", input_id=input_id, locator=locator)
    else:
        effective_to = None
    return effective_from, state, effective_to


def _jcs_string(value: str) -> str:
    chunks = ['"']
    for char in value:
        code = ord(char)
        if char == '"':
            chunks.append('\\"')
        elif char == "\\":
            chunks.append("\\\\")
        elif code in _CONTROL_ESCAPES:
            chunks.append(_CONTROL_ESCAPES[code])
        elif code < 0x20:
            chunks.append(f"\\u{code:04x}")
        else:
            chunks.append(char)
    chunks.append('"')
    return "".join(chunks)


def _jcs_dump(value: object) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int) and not isinstance(value, bool):
        if not (IJSON_INT_MIN <= value <= IJSON_INT_MAX):
            fail("NON_IJSON_INTEGER", "number")
        return "0" if value == 0 else str(value)
    if isinstance(value, str):
        if has_lone_surrogate(value):
            fail("LONE_SURROGATE", "string")
        return _jcs_string(value)
    if isinstance(value, float):
        fail("RAW_FLOAT", "number")
    if isinstance(value, list):
        return "[" + ",".join(_jcs_dump(item) for item in value) + "]"
    if isinstance(value, dict):
        keys = []
        for key in value:
            if not isinstance(key, str):
                fail("INVALID_KEY", "object")
            if has_lone_surrogate(key):
                fail("LONE_SURROGATE", "object")
            keys.append(key)
        keys.sort(key=utf16_sort_key)
        members = [_jcs_string(key) + ":" + _jcs_dump(value[key]) for key in keys]
        return "{" + ",".join(members) + "}"
    fail("UNSUPPORTED_TYPE", "value")
    raise AssertionError("unreachable")


def canonical_utf8(value: object) -> bytes:
    """Serialize a preprocessed I-JSON value under RFC 8785 JCS."""
    return _jcs_dump(value).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return sha256_hex(canonical_utf8(value))
