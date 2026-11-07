#!/usr/bin/env python3
"""Offline consumer of four narrow, revision-pinned compatibility findings.

MIT License. Copyright (c) 2026 Veyrul.
No network access, package install, media generation or project changes.
"""
import argparse
import json
from pathlib import Path


def check(feed, task):
    if feed.get('format') != 'veyrul-experimental-compatibility-feed/1':
        raise ValueError('unsupported_feed_format')
    if not isinstance(task, dict) or not isinstance(task.get('facts'), dict):
        raise ValueError('task_and_facts_must_be_objects')
    observations = []
    facts = task['facts']
    freshness = task.get('source_checks', {})
    if not isinstance(freshness, dict):
        raise ValueError('source_checks_must_be_object')
    for entry in feed['entries']:
        if entry['component'] != task.get('component'):
            continue
        source = entry['source']
        current = freshness.get(source['id'], {})
        status, reason = 'needs_evidence', None
        if not isinstance(current, dict) or current.get('public_visible') is not True:
            reason = 'source_not_confirmed_public; do not reuse private or withdrawn evidence'
        elif type(current.get('revision')) is not int or current.get('revision') != source['revision']:
            reason = 'source_revision_changed_or_unknown; re-read and review the current finding'
        elif task.get('implementation_revision') != entry['implementation_revision']:
            reason = 'implementation_revision_unverified; do not extrapolate the inspected behavior'
        elif any(k not in facts for k in entry['required_facts']):
            reason = 'required_input_facts_missing'
        else:
            name = entry['check']
            if name == 'piper_format':
                rates = [facts['voice_sample_rate'], facts['playback_sample_rate']]
                resample = facts['resample_to_hz']
                if any(type(x) is not int or x <= 0 for x in rates) or (resample is not None and (type(resample) is not int or resample <= 0)) or any(type(facts[k]) is not int or facts[k] <= 0 for k in ['sample_width_bytes','channels']):
                    status, reason = 'invalid_input', 'audio_format_fields_must_be_positive_integers'
                elif facts['sample_width_bytes'] != 2 or facts['channels'] != 1:
                    status, reason = 'warning', 'playback_format_differs_from_inspected_raw_chunk'
                elif rates[0] != rates[1] and resample != rates[1]:
                    status, reason = 'warning', 'voice_and_playback_rates_differ_without_matching_resampling'
                else:
                    status, reason = 'no_issue_detected_in_scope', 'supplied_format_and_explicit_resampling_metadata_agree; playback_not_tested'
            elif name == 'piper_latency':
                value = facts['requires_continuous_low_latency']
                if type(value) is not bool:
                    status, reason = 'invalid_input', 'latency_requirement_must_be_boolean'
                elif value:
                    reason = 'sentence_iterator_does_not_establish_a_continuous_latency_bound'
                else:
                    status, reason = 'not_applicable', 'no_continuous_latency_requirement_supplied'
            elif name == 'ass_intervals':
                values = facts['quantized_intervals_ms']
                if not isinstance(values, list) or not values or any(not isinstance(x, list) or len(x) != 2 or any(type(v) is not int for v in x) for x in values):
                    status, reason = 'invalid_input', 'expected_nonempty_integer_interval_pairs'
                elif any(start < 0 or end <= start for start, end in values):
                    status, reason = 'warning', 'negative_or_nonpositive_quantized_interval'
                else:
                    status, reason = 'no_issue_detected_in_scope', 'positive_intervals_only; full_validator_and_renderer_still_required'
            elif name == 'ass_timebase':
                changed, mapped = facts['audio_edited_after_alignment'], facts['edit_map_applied_and_checked']
                if type(changed) is not bool or type(mapped) is not bool:
                    status, reason = 'invalid_input', 'timebase_flags_must_be_booleans'
                elif changed and not mapped:
                    status, reason = 'warning', 'audio_changed_without_a_checked_time_mapping'
                else:
                    status, reason = 'no_issue_detected_in_scope', 'supplied_edit_history_has_no_unmapped_change; audio_not_inspected'
            else:
                reason = 'unsupported_rule; no arbitrary expression is executed'
        observations.append({'id': entry['id'], 'status': status, 'reason': reason, 'source': source,
                             'evidence': entry['evidence'], 'action': entry['action'], 'limits': entry['limits']})
    return {'prototype': True, 'component': task.get('component'), 'checks': observations,
            'scope': 'Caller-supplied facts and freshness; no live source verification or media inspection. An empty result is no coverage.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task', type=Path)
    args = parser.parse_args()
    feed = json.loads(Path(__file__).with_name('feed.json').read_text())
    print(json.dumps(check(feed, json.loads(args.task.read_text())), indent=2))


if __name__ == '__main__':
    main()
