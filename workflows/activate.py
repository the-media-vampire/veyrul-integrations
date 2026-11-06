#!/usr/bin/env python3
"""Activate Veyrul in a project and, for Hermes, an explicit profile. Dry-run by default."""
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile

HERE = Path(__file__).resolve().parent
BEGIN = '<!-- veyrul-workflow:begin -->'
END = '<!-- veyrul-workflow:end -->'
MAX_BYTES = 1024 * 1024
CLIENTS = {'claude-code', 'cursor', 'gemini-cli', 'opencode', 'hermes'}


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError('duplicate_json_field')
        result[key] = value
    return result


def decode(raw):
    value = json.loads(raw, object_pairs_hook=unique, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite_json_refused')))
    if not isinstance(value, dict): raise ValueError('configuration_must_be_object')
    return value


def digest(raw):
    return hashlib.sha256(raw).hexdigest() if raw is not None else None


def safe_path(root, relative):
    path = root / relative
    if path != root and root not in path.parents: raise ValueError('path_outside_project')
    current = path
    while current != root:
        if current.is_symlink(): raise ValueError('symlink_refused')
        current = current.parent
    return path


def read(path):
    if not path.exists(): return None
    if not path.is_file() or path.stat().st_size > MAX_BYTES: raise ValueError('file_scope')
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES: raise ValueError('file_scope')
    return raw


def yaml_config(raw):
    # Hermes 0.22.7 uses ruamel.yaml with YAML 1.1. Older Python environments
    # may provide PyYAML instead. Neither is installed by this helper.
    try:
        from ruamel.yaml import YAML
        from ruamel.yaml.error import YAMLError
        from ruamel.yaml.tokens import AliasToken, AnchorToken
        parser = YAML(typ='safe', pure=True); parser.version = (1, 1)
        scan, load = parser.scan, parser.load
    except ImportError:
        try: import yaml
        except ImportError: raise ValueError('yaml_parser_missing_use_hermes_python_or_manual_setup') from None
        import re
        class StrictLoader(yaml.SafeLoader): pass
        def mapping(loader, node): return unique(loader.construct_pairs(node, deep=True))
        StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
        StrictLoader.add_implicit_resolver('tag:yaml.org,2002:bool', re.compile(r'^(?:y|Y|n|N)$'), list('yYnN'))
        StrictLoader.bool_values = dict(StrictLoader.bool_values, y=True, n=False)
        YAMLError, AliasToken, AnchorToken = yaml.YAMLError, yaml.tokens.AliasToken, yaml.tokens.AnchorToken
        scan = yaml.scan
        load = lambda value: yaml.load(value, Loader=StrictLoader)
    try:
        if any(isinstance(t, (AliasToken, AnchorToken)) for t in scan(raw)):
            raise ValueError('yaml_aliases_require_manual_merge')
        value = load(raw)
        if not isinstance(value, dict): raise ValueError('configuration_must_be_object')
        def validate(item):
            if isinstance(item, dict):
                if any(not isinstance(k, str) for k in item): raise ValueError('yaml_key_requires_manual_merge')
                for child in item.values(): validate(child)
            elif isinstance(item, list):
                for child in item: validate(child)
            elif item is not None and not isinstance(item, (str, int, float, bool)):
                raise ValueError('yaml_type_requires_manual_merge')
        validate(value); json.dumps(value, allow_nan=False)
        return value
    except (YAMLError, TypeError, OverflowError, RecursionError):
        raise ValueError('yaml_requires_manual_merge') from None


def config_decode(raw, client):
    return yaml_config(raw) if client == 'hermes' else decode(raw)


def profile_root(profile):
    if profile is None: raise ValueError('explicit_hermes_profile_required')
    root = Path(profile).absolute()
    if root.is_symlink() or not root.is_dir(): raise ValueError('use_existing_profile_directory')
    return root.resolve()


def scoped_path(root, profile, path):
    scope = profile if profile is not None and path == profile / 'config.yaml' else root
    safe_path(scope, str(path.relative_to(scope)))


def display_path(root, profile, path):
    return str(path) if profile is not None and path == profile / 'config.yaml' else str(path.relative_to(root))


def server_map(config, client):
    parent = config
    if client == 'opencode':
        parent = parent.setdefault('mcp', {})
        if not isinstance(parent, dict): raise ValueError('invalid_mcp_object')
        if any(isinstance(v, dict) and ('type' in v or 'url' in v or 'command' in v) for k,v in parent.items() if k != 'servers'):
            raise ValueError('opencode_v1_configuration_requires_manual_migration')
    key = 'mcp_servers' if client == 'hermes' else 'servers' if client == 'opencode' else 'mcpServers'
    servers = parent.setdefault(key, {})
    if not isinstance(servers, dict): raise ValueError('invalid_server_map')
    return servers


def plan(project, client, workflow, mode=None, profile=None):
    root = Path(project).absolute()
    if root.is_symlink() or not root.is_dir(): raise ValueError('use_existing_project_directory')
    root = root.resolve()
    if client not in CLIENTS: raise ValueError('use_configure_for_this_client')
    if profile is not None and client != 'hermes': raise ValueError('profile_argument_is_hermes_only')
    definitions = decode((HERE / 'clients.json').read_bytes())
    workflows = {x['id']: x for x in decode((HERE / 'manifest.json').read_bytes())['workflow']}
    if workflow not in workflows or mode not in (None, 'standard', 'read-only'): raise ValueError('unknown_workflow_or_mode')
    definition = definitions[client]
    profile = profile_root(profile) if client == 'hermes' else None
    if client == 'opencode' and safe_path(root,'opencode.jsonc').exists():
        raise ValueError('existing_jsonc_configuration_use_manual_merge')
    config_path = safe_path(profile, 'config.yaml') if profile else safe_path(root, definition['file'])
    notes_path = safe_path(root, definition['instructions'])
    state_path = safe_path(root, '.veyrul/activation.json')
    ignore_path = safe_path(root, '.veyrul/.gitignore')
    ignore_raw = read(ignore_path)
    config_raw, notes_raw, state_raw = read(config_path), read(notes_path), read(state_path)
    config = config_decode(config_raw, client) if config_raw is not None else {}
    servers = server_map(config, client)
    # Reuse another existing alias instead of creating a duplicate connection.
    existing = []
    for name, item in servers.items():
        if isinstance(item, dict):
            url = item.get('url', item.get('httpUrl'))
            if isinstance(url, str) and url.rstrip('/') in ('https://veyrul.com/mcp', 'https://veyrul.com/mcp/read'):
                existing.append((name, item, 'read-only' if url.rstrip('/').endswith('/read') else 'standard'))
    if len(existing) > 1: raise ValueError('multiple_veyrul_connections_review_manually')
    # The accepted Hermes plugin is read-only. Do not silently override it.
    plugin_readonly = False
    if client == 'hermes':
        plugins = config.get('plugins', {})
        if not isinstance(plugins, dict): raise ValueError('invalid_plugins_object')
        enabled, disabled = plugins.get('enabled', []), plugins.get('disabled', [])
        if not isinstance(enabled, list) or not isinstance(disabled, list): raise ValueError('invalid_plugin_lists')
        plugin_readonly = 'veyrul-media' in enabled and 'veyrul-media' not in disabled
        if plugin_readonly and existing and existing[0][0] != 'veyrul_media':
            raise ValueError('portable_plugin_duplicate_connection_review_manually')
        if plugin_readonly and not existing and mode == 'standard':
            raise ValueError('read_only_plugin_preserved_use_explicit_native_override')
    actual_mode = existing[0][2] if existing else ('read-only' if plugin_readonly else mode or 'standard')
    if mode is not None and existing and mode != actual_mode:
        raise ValueError('existing_mode_preserved_change_connection_deliberately')
    alias = existing[0][0] if existing else 'veyrul_media'
    if not existing:
        if alias in servers: raise ValueError('existing_server_name_conflict')
        selected = deepcopy(definition['config'] if actual_mode == 'standard' else definition['read_only_config'])
        if client == 'hermes': selected = yaml_config(selected)
        servers[alias] = server_map(selected, client)['veyrul_media']
        if '$schema' in selected and '$schema' not in config: config['$schema'] = selected['$schema']
    else:
        # Never override existing authorization, tool filters, disabled state or headers.
        if existing[0][1].get('disabled') is True or existing[0][1].get('enabled') is False:
            raise ValueError('existing_connection_disabled')
    state = decode(state_raw) if state_raw is not None else {}
    if state and client == 'hermes' and state.get('profile') != str(profile):
        raise ValueError('activation_profile_conflict')
    if state and (state.get('schema') != 'veyrul-project-activation/1' or state.get('client') != client):
        raise ValueError('activation_state_conflict')
    selected_ids = sorted(set(state.get('workflows', [])) | {workflow})
    if any(x not in workflows for x in selected_ids): raise ValueError('unknown_saved_workflow')
    notes = notes_raw.decode('utf-8') if notes_raw is not None else ''
    if notes.count(BEGIN) != notes.count(END) or notes.count(BEGIN) > 1:
        raise ValueError('instruction_markers_invalid')
    old_block = None
    if BEGIN in notes:
        start, finish = notes.index(BEGIN), notes.index(END) + len(END)
        if finish < start: raise ValueError('instruction_markers_invalid')
        old_block = notes[start:finish]
        if not state or digest(old_block.encode()) != state.get('instruction_block_sha256'):
            raise ValueError('managed_instructions_changed_preserve_manual_edits')
    elif state:
        raise ValueError('managed_instructions_missing')
    rules = (HERE / ('PROJECT-INSTRUCTIONS.txt' if actual_mode == 'standard' else 'READ-ONLY-INSTRUCTIONS.txt')).read_text()
    hooks = '\n'.join('- ' + workflows[x]['name'] + ': ' + workflows[x]['use_when'] + ' ' + workflows[x]['local_work'] for x in selected_ids)
    block = BEGIN + '\n' + rules.rstrip() + '\n\nRelevant workflow hooks:\n' + hooks + '\n' + END
    updated_notes = notes.replace(old_block, block, 1) if old_block else notes + ('\n\n' if notes and not notes.endswith('\n\n') else '') + block + '\n'
    new_state = {'schema':'veyrul-project-activation/1','client':client,'mode':actual_mode,'server_alias':alias,'workflows':selected_ids,'instruction_block_sha256':digest(block.encode()),'credentials_stored':False,'tool_permissions_changed':False}
    if profile: new_state['profile'] = str(profile)
    config_new = config_raw if config_raw is not None and config_decode(config_raw, client) == config else (json.dumps(config, indent=2, ensure_ascii=False)+'\n').encode()
    proposed = [(config_path, config_raw, config_new), (notes_path, notes_raw, updated_notes.encode()), (state_path,state_raw,(json.dumps(new_state,indent=2)+'\n').encode())]
    # Local backups may contain existing credentials; exclude the entire control folder.
    ignore = ignore_raw.decode('utf-8') if ignore_raw is not None else ''
    if not ignore.splitlines() or ignore.splitlines()[-1] != '*':
        proposed.append((ignore_path, ignore_raw, (ignore + ('\n' if ignore and not ignore.endswith('\n') else '') + '*\n').encode()))
    changes = [(path, before, after) for path,before,after in proposed if before != after]
    if any(len(after)>MAX_BYTES for _,_,after in changes): raise ValueError('output_bound')
    return root, changes, {'client':client,'mode':actual_mode,'workflow_ids':selected_ids,'server_alias':alias,'files':[{'path':display_path(root,profile,path),'before_sha256':digest(before),'after_sha256':digest(after)} for path,before,after in changes], 'network_requests':0,'credentials_created':0,'permissions_changed':False,'connection_tested':False,'profile':str(profile) if profile else None,'note':'Start or reload your client and use its normal project-server approval. Existing connection restrictions remain. Contributions require your existing sharing permission and agent credential.'}


def replace(path, data):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(prefix='.veyrul-write-', dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)


def activate(project, client, workflow, mode=None, apply=False, profile=None):
    root, changes, summary = plan(project, client, workflow, mode, profile)
    profile = profile_root(profile) if client == "hermes" else None
    summary['status'] = 'unchanged' if not changes else 'planned'
    if not apply or not changes: return summary
    control = safe_path(root, '.veyrul');control.mkdir(exist_ok=True,mode=0o700)
    lock = safe_path(root, '.veyrul/activation.lock')
    try: fd = os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError: raise ValueError('activation_in_progress_or_interrupted') from None
    os.close(fd)
    written=[]
    profile_lock = None
    try:
        if profile:
            profile_lock = safe_path(profile, '.veyrul-activation.lock')
            try: fd = os.open(profile_lock, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600)
            except FileExistsError:
                profile_lock = None
                raise ValueError('profile_activation_in_progress_or_interrupted') from None
            os.close(fd)
        for path,before,_ in changes:
            scoped_path(root,profile,path)
            if read(path)!=before:raise ValueError('file_changed_during_planning')
        # Ignore backup contents before any secret-bearing old configuration is copied.
        backup_ignore=safe_path(root,'.veyrul/setup-backups/.gitignore')
        prior_ignore=read(backup_ignore)
        if prior_ignore not in (None,b'*\n'):
            raise ValueError('backup_ignore_conflict')
        if prior_ignore is None:replace(backup_ignore,b'*\n')
        # Exact private backups preserve old bytes without printing their content.
        for path,before,after in changes:
            if before is not None:
                backup=safe_path(root,'.veyrul/setup-backups/'+digest(before)+'.bak')
                if backup.exists() and read(backup)!=before:raise ValueError('backup_conflict')
                if not backup.exists():replace(backup,before)
            scoped_path(root,profile,path)
            if read(path)!=before:raise ValueError('file_changed_before_write')
            replace(path,after);written.append((path,before,after))
        summary['status']='activated';return summary
    except Exception:
        for path,before,after in reversed(written):
            scoped_path(root,profile,path)
            if not path.is_symlink() and read(path)==after:
                if before is None:path.unlink()
                else:replace(path,before)
        raise
    finally:
        if profile_lock is not None: profile_lock.unlink()
        lock.unlink()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',required=True,type=Path);p.add_argument('--client',choices=sorted(CLIENTS),required=True)
    p.add_argument('--profile',type=Path,help='Hermes only: explicit existing active profile directory; its config.yaml is changed.')
    p.add_argument('--workflow',required=True);p.add_argument('--mode',choices=['standard','read-only'])
    p.add_argument('--apply',action='store_true',help='Write the reviewed project-local configuration and instructions.')
    args=p.parse_args()
    try:print(json.dumps(activate(args.project,args.client,args.workflow,args.mode,args.apply,args.profile),indent=2))
    except (ValueError,OSError,UnicodeError) as error:
        # Do not print JSON contents or OS errors that could expose configuration data.
        code=str(error) if isinstance(error,ValueError) and str(error).replace('_','').isalnum() else 'activation_failed_review_local_files'
        p.exit(2,json.dumps({'error':code,'network_requests':0})+'\n')


if __name__=='__main__':main()
