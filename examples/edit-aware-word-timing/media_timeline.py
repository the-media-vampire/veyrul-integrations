"""Offline media timing toolkit for the fixed synthetic SPEC.txt.

Complete normalize_words, retime_words and build_events interface. Exact
peer source was inspected, hash-verified and passed 36 local test methods
before adoption. Algorithms are unchanged; application evidence and tests
are recorded in FINDINGS.json. Source: rpl_01M6FSBW2MC1TCN8AKYHFY8S87 r1;
upstream messages: rpl_01M6FRWJZPGY0N15XYQEQWWX4M r1,
rpl_01M6FRE1F0VQSYF0RN3310DMJF r1, rpl_01M6FQZYFNTEQ3SG8GHFH7NGGN r1,
rpl_01M6FQKJJNGN7J9TCVKDK5RH6M r1.

No subtitle escaping or rendering is provided. Sampling can leave retained
word occurrences unrepresented. New code is authorized for later reviewed
MIT-licensed publication; artifacts are controlled synthetic test results.
"""

from decimal import Decimal, InvalidOperation
from fractions import Fraction
import re

__all__ = ["normalize_words", "retime_words", "build_events"]

_ASCII_WHITESPACE = " \t\n\r\v\f"
_DECIMAL = re.compile(
    r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
)
_UNIT_SCALE = {"seconds": 1_000_000, "milliseconds": 1_000, "microseconds": 1}
_ROW_KEYS = {"text", "start", "end"}


def _validate_text(text):
    """Validate without stripping or Unicode-normalizing the returned text."""
    if not isinstance(text, str) or not text or not text.strip():
        raise ValueError("text must contain at least one non-whitespace character")
    if any(ord(character) < 32 or ord(character) == 127 for character in text):
        raise ValueError("text must not contain C0 controls or DEL")


def _timestamp_us(value, scale):
    """Parse the allowed decimal grammar, then round a nonnegative ratio."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError("timestamps must be integers, finite floats or decimal strings")
    token = str(value).strip(_ASCII_WHITESPACE)
    if _DECIMAL.fullmatch(token) is None:
        raise ValueError("timestamp does not match the ASCII decimal grammar")
    try:
        # Construction and as_integer_ratio are exact and do not round at the
        # caller's Decimal context precision. Avoid Decimal multiplication here.
        numerator, denominator = Decimal(token).as_integer_ratio()
    except (InvalidOperation, OverflowError, ValueError) as error:
        raise ValueError("timestamp must be a finite decimal") from error
    if numerator < 0:
        raise ValueError("timestamps must be nonnegative")
    quotient, remainder = divmod(numerator * scale, denominator)
    return quotient + int(2 * remainder >= denominator)


def normalize_words(rows, unit="seconds"):
    """Return validated words sorted by (start_us, end_us, source_index).

    Input rows have exactly text, start and end keys. Valid text is preserved
    exactly as a Python string. The source_index always references
    the original input position, even after sorting. Duplicates and overlaps
    are retained. Invalid inputs raise ValueError; inputs are never mutated.

    Accepted units are seconds, milliseconds and microseconds. Numeric inputs
    use str(value)'s exact decimal value; exact half-microseconds round upward.
    Mathematically zero values, including signed zero, are nonnegative.
    """
    if not isinstance(unit, str) or unit not in _UNIT_SCALE:
        raise ValueError("unit must be seconds, milliseconds or microseconds")
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    scale = _UNIT_SCALE[unit]
    result = []
    for source_index, row in enumerate(rows):
        if not isinstance(row, dict) or row.keys() != _ROW_KEYS:
            raise ValueError(f"row {source_index} must have exactly text, start and end keys")
        try:
            _validate_text(row["text"])
            start_us = _timestamp_us(row["start"], scale)
            end_us = _timestamp_us(row["end"], scale)
            if end_us <= start_us:
                raise ValueError("converted end_us must be greater than start_us")
        except ValueError as error:
            raise ValueError(f"row {source_index}: {error}") from error
        result.append({
            "text": row["text"],
            "source_index": source_index,
            "start_us": start_us,
            "end_us": end_us,
        })
    result.sort(key=lambda word: (word["start_us"], word["end_us"], word["source_index"]))
    return result

_WORD_KEYS = {"text", "source_index", "start_us", "end_us"}
_CUT_KEYS = {"start_us", "end_us", "speed_num", "speed_den"}


def _integer(value, name, minimum=0):
    """Validate a non-boolean integer with an inclusive lower bound."""
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")


def _round_us(value):
    """Round a nonnegative Fraction to nearest integer, exact halves upward."""
    return (2 * value.numerator + value.denominator) // (2 * value.denominator)


def retime_words(words, cuts):
    """Clip and retime every word occurrence through ordered source cuts.

    Each cut maps source time by speed_den/speed_num and starts at the exact
    sum of prior cut durations. Round absolute boundaries only; never accumulate
    rounded durations. Half-open intersections exclude touching-only words.
    Repeated and overlapping source cuts produce separate editorial occurrences.

    Both inputs are validated in full, even when either list is empty.
    Invalid input raises ValueError. Inputs and their dictionaries are unchanged.
    Stable output sorting preserves input word order for otherwise equal keys.
    Time and output space are O(len(words) * len(cuts)), plus sorting.
    """
    if not isinstance(words, list) or not isinstance(cuts, list):
        raise ValueError("words and cuts must be lists")

    for index, word in enumerate(words):
        if not isinstance(word, dict) or word.keys() != _WORD_KEYS:
            raise ValueError(f"word {index} must have exactly {_WORD_KEYS}")
        try:
            _validate_text(word["text"])
            for name in ("source_index", "start_us", "end_us"):
                _integer(word[name], name)
            if word["end_us"] <= word["start_us"]:
                raise ValueError("end_us must exceed start_us")
        except ValueError as error:
            raise ValueError(f"word {index}: {error}") from error

    for index, cut in enumerate(cuts):
        if not isinstance(cut, dict) or cut.keys() != _CUT_KEYS:
            raise ValueError(f"cut {index} must have exactly {_CUT_KEYS}")
        try:
            for name in ("start_us", "end_us"):
                _integer(cut[name], name)
            for name in ("speed_num", "speed_den"):
                _integer(cut[name], name, minimum=1)
            if cut["end_us"] <= cut["start_us"]:
                raise ValueError("end_us must exceed start_us")
        except ValueError as error:
            raise ValueError(f"cut {index}: {error}") from error

    result = []
    offset = Fraction(0)
    for cut_index, cut in enumerate(cuts):
        scale = Fraction(cut["speed_den"], cut["speed_num"])
        for word in words:
            left = max(word["start_us"], cut["start_us"])
            right = min(word["end_us"], cut["end_us"])
            if left >= right:
                continue
            start_us = _round_us(offset + (left - cut["start_us"]) * scale)
            end_us = _round_us(offset + (right - cut["start_us"]) * scale)
            if end_us <= start_us:
                continue
            result.append({
                "text": word["text"],
                "source_index": word["source_index"],
                "cut_index": cut_index,
                "start_us": start_us,
                "end_us": end_us,
            })
        offset += (cut["end_us"] - cut["start_us"]) * scale

    result.sort(key=lambda word: (
        word["start_us"], word["end_us"], word["cut_index"], word["source_index"]
    ))
    return {"words": result, "duration_us": _round_us(offset)}


_EVENT_WORD_KEYS = {"text", "source_index", "cut_index", "start_us", "end_us"}
_TICK_US = 10_000


def build_events(words, duration_us):
    """Sample highlights on the declared centisecond grid, including pauses.

    active_index addresses the original input list, never source_index,
    cut_index or a sorted position. The latest active start wins; equal starts
    use the lower input index. Intervals are half-open. The final sample is
    clamped inside the media, while the final event ends on the next grid edge.

    Every row is validated before scheduling. Unrepresented input indices
    expose both intervals missed by sampling and rows hidden by arbitration.
    This does not guarantee a highlight for every word or render subtitles.
    Inputs are unchanged. Runtime is O(words * ticks); event space is O(ticks).
    The deliberately direct scan fits the bounded study inputs.
    """
    if not isinstance(words, list):
        raise ValueError("words must be a list")
    _integer(duration_us, "duration_us")
    for index, word in enumerate(words):
        if not isinstance(word, dict) or word.keys() != _EVENT_WORD_KEYS:
            raise ValueError(f"word {index} must have exactly {_EVENT_WORD_KEYS}")
        try:
            _validate_text(word["text"])
            for name in ("source_index", "cut_index", "start_us", "end_us"):
                _integer(word[name], name)
            if word["end_us"] <= word["start_us"]:
                raise ValueError("end_us must exceed start_us")
            if word["end_us"] > duration_us:
                raise ValueError("end_us must not exceed duration_us")
        except ValueError as error:
            raise ValueError(f"word {index}: {error}") from error

    events = []
    represented = set()
    tick_count = (duration_us + _TICK_US - 1) // _TICK_US
    for tick in range(tick_count):
        sample = min(_TICK_US * tick + _TICK_US // 2, duration_us - 1)
        active_index = None
        latest_start = -1
        for index, word in enumerate(words):
            start = word["start_us"]
            if start <= sample < word["end_us"] and start > latest_start:
                # Scanning original order and ignoring equal starts retains
                # the lower input index without sorting or deduplicating.
                active_index = index
                latest_start = start
        if active_index is not None:
            represented.add(active_index)
        if events and events[-1]["active_index"] == active_index:
            events[-1]["end_cs"] = tick + 1
        else:
            events.append({"start_cs": tick, "end_cs": tick + 1,
                           "active_index": active_index})
    return {"events": events,
            "unrepresented_indices": [index for index in range(len(words))
                                      if index not in represented]}

