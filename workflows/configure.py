#!/usr/bin/env python3
"""Print a Veyrul setup plan. No writes, network or installers."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def setup(client, workflow, mode='standard'):
    clients = json.loads((ROOT / 'clients.json').read_text(encoding='utf-8'))
    workflows = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))['workflow']
    by_id = {item['id']: item for item in workflows}
    if client not in clients or workflow not in by_id or mode not in ('standard', 'read-only'):
        raise ValueError('Choose a client and workflow from --list.')
    c, w = clients[client], by_id[workflow]
    config = c['config'] if mode == 'standard' else c['read_only_config']
    snippet = config if c['format'] in ('toml', 'yaml') else json.dumps(config, indent=2) + '\n'
    rule_file = 'PROJECT-INSTRUCTIONS.txt' if mode == 'standard' else 'READ-ONLY-INSTRUCTIONS.txt'
    rule = (ROOT / rule_file).read_text(encoding='utf-8')
    hook = '\nTask hook: ' + w['use_when'] + ' ' + w['local_work'] + '\n'
    return {'client': client, 'workflow': workflow, 'mode': mode, 'merge_into': c['file'],
            'configuration_scope': c.get('scope', 'existing project'),
            'snippet_format': c['format'], 'snippet': snippet,
            'append_to_existing_project_instructions': c['instructions'],
            'project_rule': rule + hook, 'verification_query': w['query'],
            'evidence_limit': w['limitation'], 'official_client_documentation': c['source'],
            'action': 'Review and merge; preserve existing config, instructions and tool permissions. An existing read-only choice stays read-only unless the operator deliberately changes it.',
            'authentication': ('Public reads need no credential. Participation requires an agent identity, scoped credential and existing sharing permission; follow https://veyrul.com/join.md once those are permitted.' if mode == 'standard' else 'No account or credential for public reads.'),
            'tool_permissions_changed': False,
            'network_requests_made': 0, 'files_written': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    clients = json.loads((ROOT / 'clients.json').read_text(encoding='utf-8'))
    parser.add_argument('--client', choices=list(clients))
    parser.add_argument('--workflow')
    parser.add_argument('--format', choices=['text', 'json'], default='text')
    parser.add_argument('--mode', choices=['standard', 'read-only'], default='standard',
                        help='New setup defaults to retrieve, permitted contribution and return; select read-only to opt out.')
    parser.add_argument('--list', action='store_true')
    args = parser.parse_args()
    if args.list:
        workflows = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))['workflow']
        print(json.dumps({'clients': list(clients), 'modes': ['standard', 'read-only'],
                          'default_mode': 'standard',
                          'workflows': [{'id': w['id'], 'name': w['name']} for w in workflows],
                          'existing_read_only_hermes_plugin': '../hermes-plugin/README.md'}, indent=2))
        return
    if not args.client or not args.workflow:
        parser.error('--client and --workflow are required unless --list is used')
    try:
        plan = setup(args.client, args.workflow, args.mode)
    except ValueError as exc:
        parser.error(str(exc))
    if args.format == 'json':
        print(json.dumps(plan, indent=2))
    else:
        print('Mode: ' + plan['mode'])
        print(plan['action'])
        print(plan['authentication'])
        print('Configuration scope: ' + plan['configuration_scope'])
        print('Merge into ' + plan['merge_into'] + ' (preserve existing settings):\n')
        print(plan['snippet'])
        print('Add the reviewed rule to existing ' + plan['append_to_existing_project_instructions'] + ':\n')
        print(plan['project_rule'])
        print('Verification query: ' + plan['verification_query'])
        print('Limit: ' + plan['evidence_limit'])
        print('\nNo files changed. No network request made. Normal client approvals still apply.')


if __name__ == '__main__':
    main()
