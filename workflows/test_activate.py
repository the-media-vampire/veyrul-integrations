import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import activate


class ActivationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def run_activation(self,**kw):
        return activate.activate(self.root,'claude-code','soundbox',**kw)
    def test_dry_run_has_no_writes(self):
        self.assertEqual(self.run_activation()['status'],'planned');self.assertEqual(list(self.root.iterdir()),[])
    def test_default_standard(self):
        self.assertEqual(self.run_activation(apply=True)['mode'],'standard')
        self.assertEqual(json.loads((self.root/'.mcp.json').read_text())['mcpServers']['veyrul_media']['url'],'https://veyrul.com/mcp')
    def test_repeat_noop(self):
        self.run_activation(apply=True);self.assertEqual(self.run_activation(apply=True)['status'],'unchanged')
    def test_preserve_unrelated_and_secret_not_in_summary(self):
        cfg={'mcpServers':{'private':{'command':'local','env':{'API_KEY':'private-test-value'}}},'other':{'keep':True}}
        (self.root/'.mcp.json').write_text(json.dumps(cfg));out=self.run_activation(apply=True)
        actual=json.loads((self.root/'.mcp.json').read_text());self.assertEqual(actual['mcpServers']['private'],cfg['mcpServers']['private']);self.assertEqual(actual['other'],cfg['other']);self.assertNotIn('private-test-value',json.dumps(out))
        backup=next((self.root/'.veyrul/setup-backups').glob('*.bak'));self.assertEqual(backup.stat().st_mode&0o777,0o600)
    def test_notes_preserved(self):
        (self.root/'CLAUDE.md').write_text('Existing project instructions.\n');self.run_activation(apply=True);self.assertTrue((self.root/'CLAUDE.md').read_text().startswith('Existing project instructions.\n'))
    def test_add_second_hook_single_rule(self):
        self.run_activation(apply=True);out=activate.activate(self.root,'claude-code','cuttingfloor',apply=True)
        self.assertEqual(out['workflow_ids'],['cuttingfloor','soundbox']);self.assertEqual((self.root/'CLAUDE.md').read_text().count(activate.BEGIN),1)
    def test_existing_readonly_preserved_implicit(self):
        original={'mcpServers':{'other_alias':{'type':'http','url':'https://veyrul.com/mcp/read','headers':{'Authorization':'secret'}}}}
        raw=json.dumps(original).encode();(self.root/'.mcp.json').write_bytes(raw)
        out=self.run_activation(apply=True);self.assertEqual(out['mode'],'read-only');self.assertEqual(out['server_alias'],'other_alias');self.assertEqual((self.root/'.mcp.json').read_bytes(),raw)
    def test_readonly_cannot_upgrade(self):
        self.run_activation(mode='read-only',apply=True)
        with self.assertRaisesRegex(ValueError,'existing_mode_preserved'):self.run_activation(mode='standard',apply=True)
    def test_explicit_readonly(self):
        self.assertEqual(self.run_activation(mode='read-only',apply=True)['mode'],'read-only')
    def test_keep_filters(self):
        cfg={'mcpServers':{'veyrul_media':{'type':'http','url':'https://veyrul.com/mcp','tools':['search']}}};(self.root/'.mcp.json').write_text(json.dumps(cfg));self.run_activation(apply=True);self.assertEqual(json.loads((self.root/'.mcp.json').read_text()),cfg)
    def test_name_conflict(self):
        (self.root/'.mcp.json').write_text('{"mcpServers":{"veyrul_media":{"url":"https://other.invalid/mcp"}}}')
        with self.assertRaisesRegex(ValueError,'name_conflict'):self.run_activation(apply=True)
        self.assertFalse((self.root/'CLAUDE.md').exists())
    def test_multiple_connections(self):
        (self.root/'.mcp.json').write_text('{"mcpServers":{"a":{"url":"https://veyrul.com/mcp"},"b":{"url":"https://veyrul.com/mcp/read"}}}')
        with self.assertRaisesRegex(ValueError,'multiple_veyrul'):self.run_activation()
    def test_disabled_stays_disabled(self):
        (self.root/'.mcp.json').write_text('{"mcpServers":{"veyrul_media":{"url":"https://veyrul.com/mcp","disabled":true}}}')
        with self.assertRaisesRegex(ValueError,'connection_disabled'):self.run_activation(apply=True)
    def test_duplicate_keys(self):
        (self.root/'.mcp.json').write_text('{"mcpServers":{},"mcpServers":{}}')
        with self.assertRaisesRegex(ValueError,'duplicate_json'):self.run_activation()
    def test_nonfinite_json(self):
        (self.root/'.mcp.json').write_text('{"value":NaN}')
        with self.assertRaisesRegex(ValueError,'nonfinite'):self.run_activation()
    def test_opencode_jsonc_preserved(self):
        (self.root/'opencode.jsonc').write_text('// existing config\n{}')
        with self.assertRaisesRegex(ValueError,'jsonc'):activate.activate(self.root,'opencode','soundbox',apply=True)
        self.assertFalse((self.root/'opencode.json').exists())
    def test_opencode_v1_refused(self):
        (self.root/'opencode.json').write_text('{"mcp":{"existing":{"type":"remote","url":"https://example.invalid/mcp"}}}')
        with self.assertRaisesRegex(ValueError,'v1_configuration'):activate.activate(self.root,'opencode','soundbox',apply=True)
        self.assertFalse((self.root/'AGENTS.md').exists())
    def test_invalid_root(self):
        (self.root/'.mcp.json').write_text('[]')
        with self.assertRaisesRegex(ValueError,'must_be_object'):self.run_activation()
    def test_file_symlink(self):
        (self.root/'actual').write_text('{}');(self.root/'.mcp.json').symlink_to('actual')
        with self.assertRaisesRegex(ValueError,'symlink'):self.run_activation(apply=True)
    def test_parent_symlink(self):
        (self.root/'actual').mkdir();(self.root/'.veyrul').symlink_to('actual',target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'symlink'):self.run_activation(apply=True)
    def test_user_modified_block_refused(self):
        self.run_activation(apply=True);p=self.root/'CLAUDE.md';p.write_text(p.read_text().replace(activate.BEGIN,activate.BEGIN+'\nManual edit.'))
        with self.assertRaisesRegex(ValueError,'manual_edits'):self.run_activation(apply=True)
    def test_unowned_markers_refused(self):
        (self.root/'CLAUDE.md').write_text(activate.BEGIN+'\nDo not replace\n'+activate.END)
        with self.assertRaisesRegex(ValueError,'manual_edits'):self.run_activation(apply=True)
    def test_active_lock(self):
        (self.root/'.veyrul').mkdir();(self.root/'.veyrul/activation.lock').touch()
        with self.assertRaisesRegex(ValueError,'interrupted'):self.run_activation(apply=True)
    def test_rollback_after_second_write_error(self):
        original=b'{"keep":true}';(self.root/'.mcp.json').write_bytes(original)
        real=activate.replace
        def fail(path,data):
            if path.name=='CLAUDE.md':raise OSError('simulated')
            return real(path,data)
        with patch.object(activate,'replace',fail):
            with self.assertRaises(OSError):self.run_activation(apply=True)
        self.assertEqual((self.root/'.mcp.json').read_bytes(),original);self.assertFalse((self.root/'CLAUDE.md').exists());self.assertFalse((self.root/'.veyrul/activation.lock').exists());self.assertEqual((self.root/'.veyrul/setup-backups/.gitignore').read_text(),'*\n')
    def test_cursor_gemini_opencode(self):
        for client in ['cursor','gemini-cli','opencode']:
            with self.subTest(client=client):
                root=self.root/client;root.mkdir();out=activate.activate(root,client,'remotion',apply=True);self.assertEqual(out['status'],'activated');self.assertEqual(activate.activate(root,client,'remotion',apply=True)['status'],'unchanged')
    def test_unsupported_client_does_not_write(self):
        with self.assertRaisesRegex(ValueError,'configure'):activate.activate(self.root,'codex','soundbox',apply=True)
        self.assertEqual(list(self.root.iterdir()),[])

if __name__=='__main__':unittest.main()
