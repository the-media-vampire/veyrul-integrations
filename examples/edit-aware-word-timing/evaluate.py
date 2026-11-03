#!/usr/bin/env python3
"""Frozen, literal-case evaluator; never distribute this file to participants.

Usage: python3 -B evaluate.py /absolute/path/to/media_timeline.py
Only JSON goes to stdout. Exit 0 means every group passed; exit 1 means a
candidate failure; exit 2 means an evaluator/fixture setup error. Each case
uses a fresh credential-free child interpreter and a two-second execution
deadline. This is a process boundary, not an operating-system security sandbox.
Expected values below are hand-computed literals, not a reference algorithm.
"""

import argparse
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import pickle
import subprocess
import sys


SCHEMA = "veyrul-collective-media-evaluation/1"
CASE_TIMEOUT_SECONDS = 2
GROUPS = (
    "normalize_valid", "normalize_invalid", "retime_valid", "retime_invalid",
    "events_valid", "events_invalid", "empty_inputs", "no_mutation",
    "changed_edit",
)


def wire(value):
    """Preserve types: False, 0, 0.0 and tuples must not compare equal."""
    if value is None:
        return ["none"]
    if type(value) is bool:
        return ["bool", value]
    if type(value) is int:
        return ["int", str(value)]
    if type(value) is float:
        return ["float", repr(value)]
    if type(value) is str:
        return ["str", value]
    if type(value) in (list, tuple):
        return [type(value).__name__, [wire(item) for item in value]]
    if type(value) is dict:
        items = [[wire(key), wire(item)] for key, item in value.items()]
        items.sort(key=lambda item: json.dumps(item[0], ensure_ascii=True))
        return ["dict", items]
    return ["unsupported_type", type(value).__name__]


# The worker receives only a case's input, never its expected result or groups.
# Pickle decodes evaluator-owned builtins; no candidate-produced pickle is read.
WORKER = r'''
import base64, contextlib, importlib.util, json, os, pickle, sys
def wire(value):
    if value is None: return ["none"]
    if type(value) is bool: return ["bool", value]
    if type(value) is int: return ["int", str(value)]
    if type(value) is float: return ["float", repr(value)]
    if type(value) is str: return ["str", value]
    if type(value) in (list, tuple):
        return [type(value).__name__, [wire(item) for item in value]]
    if type(value) is dict:
        items = [[wire(k), wire(v)] for k, v in value.items()]
        items.sort(key=lambda item: json.dumps(item[0], ensure_ascii=True))
        return ["dict", items]
    return ["unsupported_type", type(value).__name__]
case = pickle.loads(base64.b64decode(sys.stdin.buffer.read()))
original_stdout = sys.stdout
unchanged = []
class MissingFunction(Exception): pass
def invoke(module, name, args, kwargs):
    function = getattr(module, name, None)
    if not callable(function): raise MissingFunction(name)
    before = pickle.dumps((args, kwargs), protocol=4)
    try:
        return function(*args, **kwargs)
    finally:
        unchanged.append(before == pickle.dumps((args, kwargs), protocol=4))
with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
    try:
        spec = importlib.util.spec_from_file_location("candidate_media_timeline", sys.argv[1])
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    except BaseException as error:
        outcome = {"status": "import_error", "error_type": type(error).__name__}
    else:
        try:
            if case["function"] == "pipeline":
                item = case["args"][0]
                normalized = invoke(module, "normalize_words", (item["rows"],), {"unit": item["unit"]})
                remapped = invoke(module, "retime_words", (normalized, item["cuts"]), {})
                scheduled = invoke(module, "build_events", (remapped["words"], remapped["duration_us"]), {})
                value = {"normalized": normalized, "remapped": remapped, "scheduled": scheduled}
            else:
                value = invoke(module, case["function"], case["args"], case["kwargs"])
            outcome = {"status": "returned", "value": wire(value), "unchanged": all(unchanged)}
        except MissingFunction:
            outcome = {"status": "missing_function", "unchanged": all(unchanged)}
        except BaseException as error:
            outcome = {"status": "call_error", "error_type": type(error).__name__,
                       "is_value_error": isinstance(error, ValueError), "unchanged": all(unchanged)}
original_stdout.write(json.dumps(outcome, separators=(",", ":"), ensure_ascii=True))
'''


def word(text, index, start, end):
    return {"text": text, "source_index": index, "start_us": start, "end_us": end}


def mapped(text, index, cut_index, start, end):
    return {**word(text, index, start, end), "cut_index": cut_index}


def cut(start, end, numerator=1, denominator=1):
    return {"start_us": start, "end_us": end,
            "speed_num": numerator, "speed_den": denominator}


def event(start, end, active):
    return {"start_cs": start, "end_cs": end, "active_index": active}


def cases(changed_input):
    result = []

    def add(group, name, function, args, expected=None, invalid=False, kwargs=None):
        result.append({"group": group, "id": name, "function": function,
                       "args": copy.deepcopy(tuple(args)), "kwargs": kwargs or {},
                       "expected": expected, "invalid": invalid})

    rows = [
        {"text": "same", "start": "0.020", "end": "0.030"},
        {"text": " 世界🙂 {x}\\ ", "start": "  +.0000005e0 \t", "end": "1.5e-6"},
        {"text": "same", "start": 0.02, "end": 0.03},
        {"text": "over", "start": 0.01, "end": 0.025},
        {"text": "short", "start": "0.02", "end": "0.021"},
    ]
    normalized = [word(" 世界🙂 {x}\\ ", 1, 1, 2), word("over", 3, 10000, 25000),
                  word("short", 4, 20000, 21000), word("same", 0, 20000, 30000),
                  word("same", 2, 20000, 30000)]
    add("normalize_valid", "n_order_identity_overlap_duplicates", "normalize_words", [rows], normalized)
    add("normalize_valid", "n_millisecond_halves", "normalize_words", [[
        {"text": "a", "start": ".0005", "end": ".0015"},
        {"text": "b", "start": "1.2345", "end": "2.3455"}]],
        [word("a", 0, 1, 2), word("b", 1, 1235, 2346)], kwargs={"unit": "milliseconds"})
    add("normalize_valid", "n_float_decimal_halves", "normalize_words", [[
        {"text": "a", "start": 0.0000005, "end": 0.0000015}]], [word("a", 0, 1, 2)])
    add("normalize_valid", "n_microsecond_grammar", "normalize_words", [[
        {"text": "a", "start": " -0.0 ", "end": " +1. "},
        {"text": "b", "start": ".5", "end": "2E0"},
        {"text": "c", "start": "\t1.25e+1\r\n", "end": "2E1"},
        {"text": "d", "start": "\v3.\f", "end": "4"}]],
        [word("a", 0, 0, 1), word("b", 1, 1, 2), word("d", 3, 3, 4), word("c", 2, 13, 20)],
        kwargs={"unit": "microseconds"})
    add("normalize_valid", "n_integer_seconds", "normalize_words", [[
        {"text": "a", "start": 1, "end": 2}]], [word("a", 0, 1000000, 2000000)])

    invalid_numbers = {
        "true": True, "false": False, "nan": float("nan"), "infinity": float("inf"),
        "negative_infinity": float("-inf"), "negative_fraction": -0.1, "none": None,
        "list": [], "mapping": {}, "empty": "", "point": ".", "underscore": "1_0",
        "fraction": "1/2", "hex": "0x10", "internal_space": "1 2", "nonascii_digits": "１２",
        "nonascii_space": "\u00a01\u00a0", "nan_string": "NaN", "infinity_string": "+Infinity",
        "missing_exponent": "1e+",
    }
    for field in ("start", "end"):
        for label, value in invalid_numbers.items():
            row = {"text": "valid", "start": 0, "end": 100}
            row[field] = value
            add("normalize_invalid", "n_" + field + "_" + label, "normalize_words", [[row]],
                invalid=True, kwargs={"unit": "microseconds"})
    bad_texts = {"empty": "", "blank": " \u2003 ", "newline": "a\nb", "nul": "a\0",
                 "del": "a\x7f", "number": 4, "none": None}
    for label, value in bad_texts.items():
        add("normalize_invalid", "n_text_" + label, "normalize_words",
            [[{"text": value, "start": 0, "end": 1}]], invalid=True)
    for key in ("text", "start", "end"):
        row = {"text": "a", "start": 0, "end": 1}
        del row[key]
        add("normalize_invalid", "n_missing_" + key, "normalize_words", [[row]], invalid=True)
    add("normalize_invalid", "n_extra_key", "normalize_words", [[
        {"text": "a", "start": 0, "end": 1, "confidence": 1}]], invalid=True)
    for label, value in {"none": None, "tuple": (), "mapping": {}, "string": ""}.items():
        add("normalize_invalid", "n_rows_" + label, "normalize_words", [value], invalid=True)
    for label, value in {"none": None, "list": [], "number": 4}.items():
        add("normalize_invalid", "n_row_" + label, "normalize_words", [[value]], invalid=True)
    for label, value in {"unknown": "ticks", "none": None, "list": []}.items():
        add("normalize_invalid", "n_unit_" + label, "normalize_words", [[]], invalid=True, kwargs={"unit": value})
    add("normalize_invalid", "n_collapsed_after_rounding", "normalize_words", [[
        {"text": "a", "start": "0.1", "end": "0.2"}]], invalid=True, kwargs={"unit": "microseconds"})
    add("normalize_invalid", "n_reversed", "normalize_words", [[
        {"text": "a", "start": 2, "end": 1}]], invalid=True)

    source_words = [word("C", 9, 20, 30), word("B", 2, 8, 18), word("A", 8, 0, 10),
                    word("D", 7, 10, 20), word("outside", 5, 30, 31)]
    cuts = [cut(20, 30), cut(5, 15), cut(20, 30, 2), cut(0, 10)]
    remapped = {"words": [mapped("C", 9, 0, 0, 10), mapped("A", 8, 1, 10, 15),
                          mapped("B", 2, 1, 13, 20), mapped("D", 7, 1, 15, 20),
                          mapped("C", 9, 2, 20, 25), mapped("A", 8, 3, 25, 35),
                          mapped("B", 2, 3, 33, 35)], "duration_us": 35}
    add("retime_valid", "r_repeated_out_of_order_clipping", "retime_words", [source_words, cuts], remapped)
    # Four thirds of a microsecond: only the second occurrence survives.
    add("retime_valid", "r_accumulate_thirds", "retime_words",
        [[word("a", 0, 0, 1)], [cut(0, 1, 3)] * 4],
        {"words": [mapped("a", 0, 1, 0, 1)], "duration_us": 1})
    # Three halves: absolute rounded boundaries are 0, 1, 1, 2.
    add("retime_valid", "r_absolute_halves", "retime_words",
        [[word("a", 0, 0, 1)], [cut(0, 1, 2)] * 3],
        {"words": [mapped("a", 0, 0, 0, 1), mapped("a", 0, 2, 1, 2)], "duration_us": 2})
    # Each cut lasts 20/3. The second tiny word maps 20/3..22/3 and collapses.
    add("retime_valid", "r_fractional_offset_and_speed_denominator", "retime_words",
        [[word("main", 8, 2, 8), word("tiny", 1, 0, 1)], [cut(0, 10, 3, 2)] * 2],
        {"words": [mapped("tiny", 1, 0, 0, 1), mapped("main", 8, 0, 1, 5),
                   mapped("main", 8, 1, 8, 12)], "duration_us": 13})
    add("retime_valid", "r_stable_equal_sort_keys", "retime_words", [[
        word("B", 4, 0, 5), word("A", 4, 0, 5), word("lower", 1, 0, 5)], [cut(0, 5)]],
        {"words": [mapped("lower", 1, 0, 0, 5), mapped("B", 4, 0, 0, 5),
                   mapped("A", 4, 0, 0, 5)], "duration_us": 5})

    valid_word = word("a", 2, 0, 10)
    valid_cut = cut(0, 10)
    for field in ("source_index", "start_us", "end_us"):
        for label, value in {"boolean": True, "float": 1.0, "string": "1", "negative": -1, "none": None}.items():
            item = {**valid_word, field: value}
            add("retime_invalid", "r_word_" + field + "_" + label, "retime_words", [[item], [valid_cut]], invalid=True)
    for label, value in bad_texts.items():
        add("retime_invalid", "r_text_" + label, "retime_words", [[{**valid_word, "text": value}], [valid_cut]], invalid=True)
    for key in valid_word:
        item = dict(valid_word)
        del item[key]
        add("retime_invalid", "r_word_missing_" + key, "retime_words", [[item], [valid_cut]], invalid=True)
    add("retime_invalid", "r_word_extra", "retime_words", [[{**valid_word, "cut_index": 0}], [valid_cut]], invalid=True)
    add("retime_invalid", "r_word_empty_interval", "retime_words", [[word("a", 0, 1, 1)], [valid_cut]], invalid=True)
    for field in valid_cut:
        invalids = {"boolean": True, "float": 1.0, "string": "1", "negative": -1, "none": None}
        if field in ("speed_num", "speed_den"):
            invalids["zero"] = 0
        for label, value in invalids.items():
            add("retime_invalid", "r_cut_" + field + "_" + label, "retime_words",
                [[valid_word], [{**valid_cut, field: value}]], invalid=True)
        item = dict(valid_cut)
        del item[field]
        add("retime_invalid", "r_cut_missing_" + field, "retime_words", [[valid_word], [item]], invalid=True)
    add("retime_invalid", "r_cut_extra", "retime_words", [[valid_word], [{**valid_cut, "other": 1}]], invalid=True)
    add("retime_invalid", "r_cut_empty_interval", "retime_words", [[valid_word], [cut(1, 1)]], invalid=True)
    for label, value in {"none": None, "tuple": (), "mapping": {}}.items():
        add("retime_invalid", "r_words_" + label, "retime_words", [value, [valid_cut]], invalid=True)
        add("retime_invalid", "r_cuts_" + label, "retime_words", [[valid_word], value], invalid=True)
    add("retime_invalid", "r_word_not_mapping", "retime_words", [[None], [valid_cut]], invalid=True)
    add("retime_invalid", "r_cut_not_mapping", "retime_words", [[valid_word], [None]], invalid=True)
    # Empty counterpart must not bypass validation.
    add("retime_invalid", "r_invalid_word_without_cuts", "retime_words", [[None], []], invalid=True)
    add("retime_invalid", "r_invalid_cut_without_words", "retime_words", [[], [None]], invalid=True)

    overlap = [mapped("late", 99, 5, 20000, 30000), mapped("base", 2, 1, 0, 40000),
               mapped("tie first", 1, 0, 10000, 25000), mapped("tie second", 0, 0, 10000, 25000),
               mapped("tiny", 3, 4, 100, 200)]
    scheduled = {"events": [event(0, 1, 1), event(1, 2, 2), event(2, 3, 0),
                            event(3, 4, 1), event(4, 5, None)], "unrepresented_indices": [3, 4]}
    add("events_valid", "e_overlap_unsorted_provenance_ties", "build_events", [overlap, 50000], scheduled)
    add("events_valid", "e_merge_exact_start_end", "build_events", [[mapped("a", 12, 0, 5000, 35000)], 40000],
        {"events": [event(0, 3, 0), event(3, 4, None)], "unrepresented_indices": []})
    add("events_valid", "e_half_open_and_final_clamped_sample", "build_events", [[
        mapped("a", 10, 0, 0, 5000), mapped("b", 11, 0, 5000, 15000),
        mapped("c", 12, 0, 15000, 22000), mapped("d", 13, 0, 22000, 22001)], 22001],
        {"events": [event(0, 1, 1), event(1, 2, 2), event(2, 3, 3)], "unrepresented_indices": [0]})
    add("events_valid", "e_three_microsecond_duration", "build_events", [[
        mapped("a", 3, 0, 0, 2), mapped("b", 4, 0, 2, 3)], 3],
        {"events": [event(0, 1, 1)], "unrepresented_indices": [0]})
    add("events_valid", "e_full_pause_all_words_unsampled", "build_events", [[
        mapped("a", 0, 0, 10, 11), mapped("b", 1, 0, 20000, 20001)], 25000],
        {"events": [event(0, 3, None)], "unrepresented_indices": [0, 1]})
    add("events_valid", "e_latest_active_not_latest_ended", "build_events", [[
        mapped("base", 1, 0, 0, 50000), mapped("tiny", 2, 0, 6000, 7000),
        mapped("new", 3, 0, 14000, 16000)], 50000],
        {"events": [event(0, 1, 0), event(1, 2, 2), event(2, 5, 0)], "unrepresented_indices": [1]})

    valid_mapped = mapped("a", 2, 3, 0, 10)
    for field in ("source_index", "cut_index", "start_us", "end_us"):
        for label, value in {"boolean": True, "float": 1.0, "string": "1", "negative": -1, "none": None}.items():
            add("events_invalid", "e_" + field + "_" + label, "build_events",
                [[{**valid_mapped, field: value}], 20], invalid=True)
    for label, value in bad_texts.items():
        add("events_invalid", "e_text_" + label, "build_events", [[{**valid_mapped, "text": value}], 20], invalid=True)
    for key in valid_mapped:
        item = dict(valid_mapped)
        del item[key]
        add("events_invalid", "e_missing_" + key, "build_events", [[item], 20], invalid=True)
    add("events_invalid", "e_extra", "build_events", [[{**valid_mapped, "other": 1}], 20], invalid=True)
    add("events_invalid", "e_empty_interval", "build_events", [[mapped("a", 0, 0, 1, 1)], 20], invalid=True)
    add("events_invalid", "e_end_exceeds_duration", "build_events", [[mapped("a", 0, 0, 0, 21)], 20], invalid=True)
    for label, value in {"boolean": True, "float": 20.0, "string": "20", "negative": -1, "none": None}.items():
        add("events_invalid", "e_duration_" + label, "build_events", [[], value], invalid=True)
    for label, value in {"none": None, "tuple": (), "mapping": {}}.items():
        add("events_invalid", "e_words_" + label, "build_events", [value, 20], invalid=True)
    add("events_invalid", "e_word_not_mapping", "build_events", [[None], 20], invalid=True)
    add("events_invalid", "e_invalid_word_zero_duration", "build_events", [[None], 0], invalid=True)

    add("empty_inputs", "empty_normalize", "normalize_words", [[]], [])
    add("empty_inputs", "empty_normalize_milliseconds", "normalize_words", [[]], [], kwargs={"unit": "milliseconds"})
    add("empty_inputs", "empty_retime_both", "retime_words", [[], []], {"words": [], "duration_us": 0})
    add("empty_inputs", "empty_cuts", "retime_words", [[valid_word], []], {"words": [], "duration_us": 0})
    add("empty_inputs", "empty_words_keep_duration", "retime_words", [[], [cut(0, 1, 2)] * 3],
        {"words": [], "duration_us": 2})
    add("empty_inputs", "empty_events_zero", "build_events", [[], 0], {"events": [], "unrepresented_indices": []})
    add("empty_inputs", "empty_events_pause", "build_events", [[], 25001],
        {"events": [event(0, 3, None)], "unrepresented_indices": []})

    add("no_mutation", "mutation_normalize_unsorted", "normalize_words", [rows], normalized)
    add("no_mutation", "mutation_retime_unsorted", "retime_words", [source_words, cuts], remapped)
    add("no_mutation", "mutation_events_unsorted", "build_events", [overlap, 50000], scheduled)
    add("no_mutation", "mutation_normalize_before_error", "normalize_words", [[rows[0], {"text": "bad"}]], invalid=True)
    add("no_mutation", "mutation_retime_before_error", "retime_words", [[valid_word, None], [valid_cut]], invalid=True)
    add("no_mutation", "mutation_events_before_error", "build_events", [[valid_mapped, None], 20], invalid=True)

    # Changed cut offsets are 0, 80000/3, 170000/3, 250000/3;
    # total = 430000/3 -> 143333. Expected outputs are literal hand arithmetic.
    changed_normalized = [word(" hello ", 1, 0, 30000), word(" hello ", 5, 0, 30000),
                          word("{tiny}\\x", 3, 1000, 1004), word("世界", 2, 20000, 50000),
                          word("boundary", 6, 50000, 60000), word("🙂 later", 0, 60000, 90000),
                          word("tail", 4, 90000, 110000)]
    changed_remapped = {"words": [
        mapped("🙂 later", 0, 0, 0, 20000), mapped("tail", 4, 0, 20000, 26667),
        mapped(" hello ", 1, 1, 26667, 41667), mapped(" hello ", 5, 1, 26667, 41667),
        mapped("{tiny}\\x", 3, 1, 27167, 27169), mapped("世界", 2, 1, 36667, 51667),
        mapped("boundary", 6, 1, 51667, 56667), mapped("🙂 later", 0, 2, 56667, 76667),
        mapped("tail", 4, 2, 76667, 83333), mapped(" hello ", 1, 3, 83333, 93333),
        mapped(" hello ", 5, 3, 83333, 93333), mapped("世界", 2, 3, 83333, 133333),
        mapped("boundary", 6, 3, 133333, 143333)], "duration_us": 143333}
    changed_scheduled = {"events": [event(0, 2, 0), event(2, 3, 1), event(3, 4, 2),
                                    event(4, 5, 5), event(5, 6, 6), event(6, 8, 7),
                                    event(8, 9, 9), event(9, 13, 11), event(13, 15, 12)],
                         "unrepresented_indices": [3, 4, 8, 10]}
    add("changed_edit", "changed_complete_pipeline", "pipeline", [changed_input],
        {"normalized": changed_normalized, "remapped": changed_remapped, "scheduled": changed_scheduled})
    return result


def run_case(module_path, case, timeout=CASE_TIMEOUT_SECONDS):
    payload = {key: case[key] for key in ("function", "args", "kwargs")}
    environment = {"PATH": os.defpath, "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
                   "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        process = subprocess.run([sys.executable, "-I", "-B", "-c", WORKER, str(module_path)],
                                 input=base64.b64encode(pickle.dumps(payload, protocol=4)),
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                 cwd=str(module_path.parent), env=environment, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    except OSError:
        return {"status": "worker_start_error"}
    if process.returncode != 0:
        return {"status": "worker_crash", "returncode": process.returncode}
    if len(process.stdout) > 131072:
        return {"status": "oversized_result"}
    try:
        return json.loads(process.stdout)
    except (ValueError, UnicodeError):
        return {"status": "malformed_worker_result"}


def judge(case, observed):
    status = observed.get("status")
    if status not in ("returned", "call_error"):
        return False, status or "missing_worker_status"
    if observed.get("unchanged") is not True:
        return False, "input_mutated"
    if case["invalid"]:
        if status == "call_error" and observed.get("is_value_error") is True:
            return True, "expected_value_error"
        return False, "expected_value_error_got_" + observed.get("error_type", status)
    if status != "returned":
        return False, "unexpected_" + observed.get("error_type", status)
    if observed.get("value") != wire(case["expected"]):
        return False, "wrong_value_or_structure"
    return True, "matched"


def evaluate(module_path, selected_cases):
    groups = {group: {"passed": 0, "total": 0, "ok": False, "failures": []} for group in GROUPS}
    for case in selected_cases:
        observed = run_case(module_path, case)
        ok, reason = judge(case, observed)
        group = groups[case["group"]]
        group["total"] += 1
        group["passed"] += int(ok)
        if not ok:
            group["failures"].append({"id": case["id"], "reason": reason})
    for group in groups.values():
        group["ok"] = group["total"] > 0 and group["passed"] == group["total"]
    return {"schema": SCHEMA, "accepted": all(group["ok"] for group in groups.values()),
            "passed_groups": sum(group["ok"] for group in groups.values()), "total_groups": len(GROUPS),
            "passed_cases": sum(group["passed"] for group in groups.values()),
            "total_cases": sum(group["total"] for group in groups.values()),
            "primary_changed_edit_passed": groups["changed_edit"]["ok"],
            "case_timeout_seconds": CASE_TIMEOUT_SECONDS, "groups": groups}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module", type=Path)
    arguments = parser.parse_args()
    fixture_path = Path(__file__).with_name("CHANGED-EDIT.json")
    try:
        changed_bytes = fixture_path.read_bytes()
        selected_cases = cases(json.loads(changed_bytes))
        if len({case["id"] for case in selected_cases}) != len(selected_cases):
            raise ValueError("duplicate_case_identifier")
        module_path = arguments.module.resolve()
        output = evaluate(module_path, selected_cases)
        output["changed_input_sha256"] = hashlib.sha256(changed_bytes).hexdigest()
        output["evaluator_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        output["artifact_sha256"] = hashlib.sha256(module_path.read_bytes()).hexdigest() if module_path.is_file() else None
    except Exception as error:
        print(json.dumps({"schema": SCHEMA, "status": "evaluator_error", "error_type": type(error).__name__}, separators=(",", ":")))
        return 2
    print(json.dumps(output, separators=(",", ":"), ensure_ascii=True))
    return 0 if output["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
