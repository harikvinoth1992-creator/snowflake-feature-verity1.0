import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
from render_config import render, valid_config  # noqa: E402


class DeploymentConfigTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT/'config/verity.deployment.example.json').read_text())

    def test_example_renders_without_external_packages(self):
        with tempfile.TemporaryDirectory() as temp:
            cfg = Path(temp)/'config.json'
            cfg.write_text(json.dumps(self.config))
            out = Path(temp)/'generated'
            render(cfg, out)
            self.assertIn('NO USERS CONFIGURED', (out/'12_grants/08_assign_roles_to_users.sql').read_text())
            self.assertTrue((out/'deployment_manifest.configured.json').is_file())
            self.assertIn('NO APPROVED PROJECT SOURCES', (out/'12_grants/02_project_approved_sources.sql').read_text())

    def test_user_and_source_parameterized(self):
        self.config['role_assignments']['runtime_de_users'] = ['CLIENT_ETL_USER']
        self.config['roles']['runtime_project_de'] = 'CLIENT_RUNTIME_ROLE'
        self.config['project_sources'][0]['approved'] = True
        with tempfile.TemporaryDirectory() as temp:
            cfg = Path(temp)/'config.json'
            cfg.write_text(json.dumps(self.config))
            out = Path(temp)/'out'
            render(cfg, out)
            assign = (out/'12_grants/08_assign_roles_to_users.sql').read_text()
            project = (out/'12_grants/02_project_approved_sources.sql').read_text()
            base = (out/'12_grants/01_project_runtime_hardened_base.sql').read_text()
            self.assertIn('GRANT ROLE CLIENT_RUNTIME_ROLE TO USER CLIENT_ETL_USER;', assign)
            self.assertIn('GRANT SELECT ON TABLE DE_PIPELINE_POC_DB.LAB.ORDER_FULFILMENT TO ROLE CLIENT_RUNTIME_ROLE;', project)
            self.assertIn('TO ROLE CLIENT_RUNTIME_ROLE;', base)
            self.assertNotIn('GRANT INSERT ON TABLE VERITY_V1_0.CONFIG.DQ_RULE_CATALOG', base)

    def test_rejects_identifier_injection(self):
        self.config['role_assignments']['viewer_users']=['GOOD; DROP DATABASE VERITY_V1_0']
        with self.assertRaises(ValueError):
            valid_config(self.config)

    def test_block_unsafe_name_rename(self):
        self.config['database']='CLIENT_DB'
        with self.assertRaises(ValueError):
            valid_config(self.config)

    def test_task_cannot_autostart(self):
        self.config['scheduled_task']['enabled_on_install']=True
        with self.assertRaises(ValueError):
            valid_config(self.config)


if __name__=='__main__':
    unittest.main()
