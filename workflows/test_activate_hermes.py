import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import activate

class HermesActivation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.project = self.root/'project'; self.project.mkdir()
        self.profile = self.root/'profile'; self.profile.mkdir()
        self.config = self.profile/'config.yaml'
    def run_setup(self, **kwargs):
        return activate.activate(self.project, 'hermes', 'hermes', profile=self.profile, **kwargs)
    def test_explicit_profile(self):
        with self.assertRaisesRegex(ValueError,'explicit_hermes_profile'):activate.activate(self.project,'hermes','hermes')
    def test_preview_changes_nothing(self):
        self.assertEqual(self.run_setup()['status'],'planned')
        self.assertEqual(list(self.profile.iterdir()),[]);self.assertEqual(list(self.project.iterdir()),[])
    def test_fresh_standard_and_noop(self):
        result=self.run_setup(apply=True)
        server=activate.yaml_config(self.config.read_bytes())['mcp_servers']['veyrul_media']
        self.assertEqual(server['url'],'https://veyrul.com/mcp');self.assertEqual(server['trust'],'untrusted')
        self.assertIn('collaboration_post_message',server['tools']['include'])
        self.assertFalse(result['connection_tested']);self.assertEqual(self.run_setup(apply=True)['status'],'unchanged')
    def test_preserve_yaml_settings_and_backup(self):
        raw=b'# original comment\nmodel:\n  default: keep-model\nmcp_servers:\n  other:\n    url: https://example.invalid/mcp\n    headers:\n      Authorization: test-secret-never-print\n'
        self.config.write_bytes(raw); result=self.run_setup(apply=True)
        cfg=activate.yaml_config(self.config.read_bytes());self.assertEqual(cfg['model']['default'],'keep-model')
        self.assertEqual(cfg['mcp_servers']['other']['headers']['Authorization'],'test-secret-never-print')
        self.assertNotIn('test-secret',json.dumps(result))
        backup=self.project/'.veyrul/setup-backups'/f'{activate.digest(raw)}.bak'
        self.assertEqual(backup.read_bytes(),raw);self.assertEqual(backup.stat().st_mode&0o777,0o600)
    def test_existing_profile_keeps_bytes_and_filters(self):
        raw=b'# preserve this comment\nmcp_servers:\n  my_media:\n    url: https://veyrul.com/mcp\n    tools:\n      include: [search]\n    headers:\n      Authorization: test-private\n'
        self.config.write_bytes(raw); result=self.run_setup(apply=True)
        self.assertEqual(result['server_alias'],'my_media');self.assertEqual(self.config.read_bytes(),raw)
    def test_catalogue_plugin_stays_readonly(self):
        self.config.write_text('plugins:\n  enabled: [veyrul-media]\n')
        self.assertEqual(self.run_setup(apply=True)['mode'],'read-only')
        self.assertNotIn('automatically contribute',(self.project/'AGENTS.md').read_text())
    def test_catalogue_plugin_not_silently_upgraded(self):
        self.config.write_text('plugins:\n  enabled: [veyrul-media]\n')
        before=self.config.read_bytes()
        with self.assertRaisesRegex(ValueError,'native_override'):self.run_setup(mode='standard',apply=True)
        self.assertEqual(before,self.config.read_bytes());self.assertFalse((self.project/'AGENTS.md').exists())
    def test_explicit_participation_preview_and_install(self):
        self.config.write_text('plugins: {enabled: [veyrul-media]}\nmodel: {default: keep}\n')
        before=self.config.read_bytes()
        self.assertEqual(self.run_setup(enable_participation=True)['mode'],'standard')
        self.assertEqual(self.config.read_bytes(),before)
        self.run_setup(enable_participation=True,apply=True)
        cfg=activate.yaml_config(self.config.read_bytes());server=cfg['mcp_servers']['veyrul_media']
        self.assertEqual(server['url'],'https://veyrul.com/mcp')
        self.assertEqual(server['trust'],'untrusted')
        self.assertEqual(cfg['model']['default'],'keep')
        self.assertNotIn('request_resident',server['tools']['include'])
        self.assertNotIn('start_investigation',server['tools']['include'])
        self.assertEqual(self.run_setup(enable_participation=True,apply=True)['status'],'unchanged')
    def test_explicit_participation_preserves_existing_restrictions(self):
        self.config.write_text('plugins: {enabled: [veyrul-media]}\nmcp_servers: {veyrul_media: {url: https://veyrul.com/mcp/read}}\n')
        before=self.config.read_bytes()
        with self.assertRaisesRegex(ValueError,'existing_mode'):self.run_setup(enable_participation=True,apply=True)
        self.assertEqual(self.config.read_bytes(),before)
    def test_participation_conflicting_mode_refused(self):
        with self.assertRaisesRegex(ValueError,'participation_requires'):self.run_setup(enable_participation=True,mode='read-only',apply=True)
    def test_yaml11_yes_no_letters(self):
        self.config.write_text('feature: y\nother: n\n')
        self.run_setup(apply=True);cfg=activate.yaml_config(self.config.read_bytes())
        self.assertIs(cfg['feature'],True);self.assertIs(cfg['other'],False)
    def test_plugin_and_different_alias_refused(self):
        self.config.write_text('plugins: {enabled: [veyrul-media]}\nmcp_servers:\n  other_alias: {url: https://veyrul.com/mcp}\n')
        with self.assertRaisesRegex(ValueError,'duplicate_connection'):self.run_setup(apply=True)
    def test_existing_readonly_preserved(self):
        self.config.write_text('mcp_servers:\n  v:\n    url: https://veyrul.com/mcp/read\n')
        self.assertEqual(self.run_setup(apply=True)['mode'],'read-only')
        with self.assertRaisesRegex(ValueError,'existing_mode'):self.run_setup(mode='standard',apply=True)
    def test_native_override_takes_precedence(self):
        self.config.write_text('plugins:\n  enabled: [veyrul-media]\nmcp_servers:\n  veyrul_media:\n    url: https://veyrul.com/mcp\n    trust: untrusted\n')
        self.assertEqual(self.run_setup(apply=True)['mode'],'standard')
    def test_disabled_server_refused(self):
        self.config.write_text('mcp_servers:\n  v:\n    url: https://veyrul.com/mcp\n    enabled: false\n')
        with self.assertRaisesRegex(ValueError,'disabled'):self.run_setup(apply=True)
    def test_duplicate_yaml_refused(self):
        self.config.write_text('model: one\nmodel: two\n')
        with self.assertRaisesRegex(ValueError,'duplicate|manual_merge'):self.run_setup(apply=True)
    def test_alias_yaml_refused(self):
        self.config.write_text('model: &m {default: test}\nother: *m\n')
        with self.assertRaisesRegex(ValueError,'aliases'):self.run_setup(apply=True)
    def test_dates_nonfinite_and_nonstrings_refused(self):
        for value in ['a: 2026-11-06\n','a: .inf\n','true: invalid\n']:
            self.config.write_text(value)
            with self.assertRaises(ValueError):self.run_setup(apply=True)
    def test_profile_symlink_refused(self):
        link=self.root/'profile-link';link.symlink_to(self.profile,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'profile_directory'):activate.activate(self.project,'hermes','hermes',profile=link,apply=True)
    def test_config_symlink_refused(self):
        outside=self.root/'outside';outside.write_text('{}');self.config.symlink_to(outside)
        with self.assertRaisesRegex(ValueError,'symlink'):self.run_setup(apply=True)
        self.assertEqual(outside.read_text(),'{}')
    def test_profile_lock_preserved(self):
        lock=self.profile/'.veyrul-activation.lock';lock.write_text('another-writer')
        with self.assertRaisesRegex(ValueError,'profile_activation'):self.run_setup(apply=True)
        self.assertEqual(lock.read_text(),'another-writer');self.assertFalse(self.config.exists())
        self.assertFalse((self.project/'.veyrul/activation.lock').exists())
    def test_failure_restores_yaml_exactly(self):
        raw=b'# keep comment\nmodel: {default: keep}\n';self.config.write_bytes(raw)
        real=activate.replace
        def fail(path,data):
            if path.name=='AGENTS.md':raise OSError('simulated')
            return real(path,data)
        with patch.object(activate,'replace',fail):
            with self.assertRaises(OSError):self.run_setup(apply=True)
        self.assertEqual(raw,self.config.read_bytes());self.assertFalse((self.profile/'.veyrul-activation.lock').exists())
    def test_second_project_reuses_profile(self):
        self.run_setup(apply=True);before=self.config.read_bytes();other=self.root/'other';other.mkdir()
        activate.activate(other,'hermes','soundbox',profile=self.profile,apply=True)
        self.assertEqual(before,self.config.read_bytes());self.assertTrue((other/'AGENTS.md').exists())
    def test_saved_profile_conflict(self):
        self.run_setup(apply=True);other=self.root/'other-profile';other.mkdir()
        with self.assertRaisesRegex(ValueError,'profile_conflict'):activate.activate(self.project,'hermes','hermes',profile=other,apply=True)
        self.assertFalse((other/'config.yaml').exists())
    def test_existing_project_rules_preserved_and_edits_refused(self):
        notes=self.project/'AGENTS.md';notes.write_text('Keep existing project policy.\n')
        self.run_setup(apply=True);self.assertTrue(notes.read_text().startswith('Keep existing project policy.\n'))
        notes.write_text(notes.read_text().replace(activate.BEGIN,activate.BEGIN+'\nManual edit.'))
        with self.assertRaisesRegex(ValueError,'manual_edits'):self.run_setup(apply=True)

if __name__=='__main__':unittest.main()
