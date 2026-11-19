import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from render_config import render, valid_config, render_sql_template

class TemplateBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads((ROOT/'config/verity.deployment.example.json').read_text())

    def run_render(self, cfg):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root=Path(temp.name)
        p=root/'c.json'; p.write_text(json.dumps(cfg))
        out=root/'generated'; render(p,out)
        return out

    def test_no_implicit_admin_to_current_user(self):
        out=self.run_render(self.cfg)
        r=(out/'01_roles/02_role_hierarchy_and_bootstrap.sql').read_text()
        self.assertIn('GRANT ROLE VERITY_V1_0_EXEC_DE_PIPELINE TO ROLE VERITY_V1_0_ADMIN;',r)
        self.assertIn('GRANT ROLE VERITY_V1_0_ADMIN TO ROLE SYSADMIN;',r)
        self.assertNotIn('SET VERITY_USER',r)
        self.assertNotIn('GRANT ROLE VERITY_V1_0_STEWARD TO USER',r)
        self.assertNotIn('GRANT ROLE VERITY_V1_0_TASK_EXEC TO USER',r)

    def test_self_grant_opt_in(self):
        cfg=copy.deepcopy(self.cfg)
        cfg['bootstrap']['grant_admin_to_current_user']=True
        cfg['roles']['admin']='CLIENT_DQ_ADMIN'
        cfg['roles']['runtime_project_de']='CLIENT_DQ_RUNTIME'
        out=self.run_render(cfg)
        r=(out/'01_roles/02_role_hierarchy_and_bootstrap.sql').read_text()
        self.assertIn('GRANT ROLE CLIENT_DQ_RUNTIME TO ROLE CLIENT_DQ_ADMIN;',r)
        self.assertIn('GRANT ROLE CLIENT_DQ_ADMIN TO ROLE SYSADMIN;',r)
        self.assertIn('SET VERITY_USER = (SELECT CURRENT_USER());',r)
        self.assertIn('GRANT ROLE CLIENT_DQ_ADMIN TO USER IDENTIFIER($VERITY_USER);',r)
        self.assertNotIn('{{',r)
        m=json.loads((out/'deployment_manifest.configured.json').read_text())
        files=next(x['files'] for x in m['phases'] if x['phase']=='01')
        self.assertEqual(len(files),2)

    def test_hierarchy_opt_out(self):
        cfg=copy.deepcopy(self.cfg)
        cfg['bootstrap']['runtime_under_admin']=False
        cfg['bootstrap']['admin_under_sysadmin']=False
        out=self.run_render(cfg)
        r=(out/'01_roles/02_role_hierarchy_and_bootstrap.sql').read_text()
        self.assertNotIn('TO ROLE SYSADMIN;',r)
        self.assertNotIn('TO ROLE VERITY_V1_0_ADMIN;',r)

    def test_rejects_invalid_bootstrap_type(self):
        cfg=copy.deepcopy(self.cfg)
        cfg['bootstrap']['grant_admin_to_current_user']='true; DROP ROLE x'
        with self.assertRaises(ValueError): valid_config(cfg)

    def test_fails_closed_for_unknown_template_variable(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'template.sql.j2'; p.write_text('SELECT {{ something_unsafe }};')
            with self.assertRaises(ValueError): render_sql_template(p,{'admin_role':'SAFE'})

if __name__=='__main__': unittest.main()
