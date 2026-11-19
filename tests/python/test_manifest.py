import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class ManifestTests(unittest.TestCase):
 def test_phase_names(self):
  m=json.loads((ROOT/'deploy/deployment_manifest.json').read_text())
  self.assertEqual([x['phase'] for x in m['phases']], [f'{i:02d}' for i in range(17)])
 def test_manifest_paths_are_unique_and_safe(self):
  m=json.loads((ROOT/'config/object_manifest.json').read_text())
  seen=[]
  for o in m['objects']:
   p=o['path'];self.assertTrue(p.startswith('sql/'));self.assertNotIn('..',p);
   if not o.get("metadata_only"): seen.append(p)
  self.assertEqual(len(seen),len(set(seen)))
 def test_known_critical_objects(self):
  m=json.loads((ROOT/'config/object_manifest.json').read_text())
  kinds={x['type'] for x in m['objects'] if x['required']}
  self.assertTrue({'TABLE','PROCEDURE','VIEW','STREAM','TASK'}<=kinds)
if __name__=='__main__': unittest.main()
