"""Strict validation adapter around the unmodified upstream frame_rule_checker.

Upstream: the-media-vampire/veyrul-lab @ d33f5b0b2af6cbe420483d04543995cd9ef3d3c7
          frame_rule_checker.py, sha256 d0a3dca8f29522ae97527db216d0bbdbd5cb641d40fb64f9c8eab677a6e3766e

The upstream file is loaded by path and never edited. This adapter only rejects
inputs that upstream would silently score, then delegates verdicts to upstream
check(). It adds no semantic or visual judgement.
"""
import hashlib
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
UPSTREAM_PATH = os.path.join(HERE, "upstream", "frame_rule_checker.py")
UPSTREAM_SHA256 = "d0a3dca8f29522ae97527db216d0bbdbd5cb641d40fb64f9c8eab677a6e3766e"

CHECK_TYPES = ("boolean", "exact", "contains")
CONFIDENCES = ("clear", "partial", "unclear")


class ValidationError(ValueError):
    pass


def load_upstream(path=UPSTREAM_PATH):
    with open(path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    if digest != UPSTREAM_SHA256:
        raise ValidationError(f"upstream sha256 mismatch: {digest}")
    spec = importlib.util.spec_from_file_location("frame_rule_checker_d33f5b0b", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


upstream = load_upstream()
Rule = upstream.Rule
FrameObs = upstream.FrameObs


def _nonblank_str(value, what):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{what} must be a non-blank string, got {value!r}")


def validate_rule(rule):
    _nonblank_str(rule.rule_id, "rule_id")
    _nonblank_str(rule.description, f"{rule.rule_id}: description")
    if rule.check_type not in CHECK_TYPES:
        raise ValidationError(f"{rule.rule_id}: unknown check_type {rule.check_type!r}")
    if rule.check_type == "boolean" and type(rule.expected) is not bool:
        raise ValidationError(f"{rule.rule_id}: boolean rule needs expected True/False, got {rule.expected!r}")
    if rule.check_type == "contains":
        _nonblank_str(rule.expected, f"{rule.rule_id}: contains expected")
    if rule.check_type == "exact":
        if rule.expected is None or isinstance(rule.expected, bool):
            raise ValidationError(f"{rule.rule_id}: exact rule needs a non-bool, non-None expected value")
        if isinstance(rule.expected, str):
            _nonblank_str(rule.expected, f"{rule.rule_id}: exact expected")


def validate_obs(rule, obs):
    if obs.rule_id != rule.rule_id:
        raise ValidationError(f"observation id {obs.rule_id!r} does not match rule {rule.rule_id!r}")
    if obs.confidence not in CONFIDENCES:
        raise ValidationError(f"{rule.rule_id}: unknown confidence {obs.confidence!r}")
    v = obs.observed
    if v is None:
        # Explicit "not observed" stays allowed; upstream maps it to NOT_VERIFIED.
        return
    if isinstance(v, str) and not v.strip():
        raise ValidationError(f"{rule.rule_id}: blank observed state; use None for not observed")
    if rule.check_type == "boolean" and type(v) is not bool:
        # Upstream uses bool(v): bool("false") and bool("no") are True.
        raise ValidationError(f"{rule.rule_id}: boolean observation must be True/False, got {v!r}")
    if rule.check_type == "exact" and isinstance(v, bool):
        # Upstream compares with ==, so True == 1 would MATCH an expected count of 1.
        raise ValidationError(f"{rule.rule_id}: bool observation for exact rule, got {v!r}")
    if rule.check_type == "exact" and type(v) is not type(rule.expected):
        raise ValidationError(f"{rule.rule_id}: observed type {type(v).__name__} != expected {type(rule.expected).__name__}")
    if rule.check_type == "contains" and not isinstance(v, str):
        raise ValidationError(f"{rule.rule_id}: contains observation must be a string, got {v!r}")


def strict_check(rule, obs):
    validate_rule(rule)
    validate_obs(rule, obs)
    return upstream.check(rule, obs)


def strict_score_clip(rules, observations):
    """Validated score_clip: unique rule IDs, at most one observation per rule,
    no orphan observations. Missing observations stay NOT_VERIFIED (as upstream)."""
    seen = set()
    for r in rules:
        validate_rule(r)
        if r.rule_id in seen:
            raise ValidationError(f"duplicate rule id {r.rule_id!r}")
        seen.add(r.rule_id)
    obs_ids = [o.rule_id for o in observations]
    dupes = sorted({i for i in obs_ids if obs_ids.count(i) > 1})
    if dupes:
        raise ValidationError(f"duplicate observations for {dupes}")
    orphans = sorted(set(obs_ids) - seen)
    if orphans:
        raise ValidationError(f"observations without a rule: {orphans}")
    by_id = {o.rule_id: o for o in observations}
    for r in rules:
        if r.rule_id in by_id:
            validate_obs(r, by_id[r.rule_id])
    return upstream.score_clip(rules, observations)
