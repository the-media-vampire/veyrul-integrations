#!/usr/bin/env python3
"""Print a reviewed, project-scoped setup plan. No writes, network or installers."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def setup(client, workflow):
    clients = json.loads((ROOT / 'clients.json').read_text(encoding='utf-8'))
    workflows = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))['workflow']
    by_id = {item['id']: item for item in workflows}
    if client not in clients or workflow not in by_id:
        raise ValueError('Choose a client and workflow from --list.')
    c, w = clients[client], by_id[workflow]
    snippet = c['config'] if c['format'] == 'toml' else json.dumps(c['config'], indent=2) + '\n'
    rule = (ROOT / 'PROJECT-INSTRUCTIONS.txt').read_text(encoding='utf-8')
    hook = '\nTask hook: ' + w['use_when'] + ' ' + w['local_work'] + '\n'
    return {'client': client, 'workflow': workflow, 'merge_into': c['file'],
            'snippet_format': c['format'], 'snippet': snippet,
            'append_to_existing_project_instructions': c['instructions'],
            'project_rule': rule + hook, 'verification_query': w['query'],
            'evidence_limit': w['limitation'], 'official_client_documentation': c['source'],
            'action': 'Review and merge; preserve existing config, instructions and tool permissions.',
            'network_requests_made': 0, 'files_written': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', choices=['codex', 'claude-code', 'cursor', 'gemini-cli'])
    parser.add_argument('--workflow')
    parser.add_argument('--format', choices=['text', 'json'], default='text')
    parser.add_argument('--list', action='store_true')
    args = parser.parse_args()
    if args.list:
        workflows = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))['workflow']
        print(json.dumps({'clients': ['codex', 'claude-code', 'cursor', 'gemini-cli'],
                          'workflows': [{'id': w['id'], 'name': w['name']} for w in workflows],
                          'hermes': '../hermes-plugin/README.md'}, indent=2))
        return
    if not args.client or not args.workflow:
        parser.error('--client and --workflow are required unless --list is used')
    try:
        plan = setup(args.client, args.workflow)
    except ValueError as exc:
        parser.error(str(exc))
    if args.format == 'json':
        print(json.dumps(plan, indent=2))
    else:
        print('Merge into ' + plan['merge_into'] + ' (preserve existing settings):\n')
        print(plan['snippet'])
        print('Add the reviewed rule to existing ' + plan['append_to_existing_project_instructions'] + ':\n')
        print(plan['project_rule'])
        print('Verification query: ' + plan['verification_query'])
        print('Limit: ' + plan['evidence_limit'])
        print('\nNo files changed. No network request made. Normal client approvals still apply.')


if __name__ == '__main__':
    main()
