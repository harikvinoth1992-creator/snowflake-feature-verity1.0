#!/usr/bin/env python3
"""Strict offline release gate; NEVER connects to Snowflake or changes objects."""
import csv,json,re,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
m=json.loads((root/'config/object_manifest.json').read_text())
errors=[]; warnings=[]
if not (root/'inventory/source_inventory.csv').exists():
 errors.append('Real source_inventory.csv missing: cannot prove object completeness')
else:
 with (root/'inventory/source_inventory.csv').open(newline='',encoding='utf-8-sig') as f:
  rows=list(csv.DictReader(f))
 if not rows: errors.append('Source inventory file is empty')
 byname={row.get('fully_qualified_name','').strip().upper():row for row in rows}
 for o in m['objects']:
  if o['required'] and o['name'].upper() not in byname:
   errors.append('Required object missing from SOURCE inventory: '+o['name'])
 paths={o['name'].upper():o.get('path') for o in m['objects']}
 for n,row in byname.items():
  if not n: errors.append('Source inventory has unnamed object');continue
  if n not in paths:
   errors.append('Unmapped EXTRA LIVE source object: '+n+'; add it to manifest with deploy path')
  if row.get('source_ddl_captured','').strip().lower() not in ('true','yes','1'):
   errors.append('Source inventory marks DDL not captured: '+n)
for o in m['objects']:
 p=root/o['path']
 if not p.is_file():
  if o['required'] or (o['name'].upper() in (byname if 'byname' in locals() else {})):
   errors.append('Missing captured SQL for source object: '+str(p.relative_to(root)))
  else: warnings.append('Optional/unverified object lacks DDL: '+o['name'])
  continue
 if o.get('metadata_only'):
  continue
 s=p.read_text(encoding='utf-8-sig',errors='replace').strip()
 if len(s)<35 or 'CREATE' not in s.upper():
  errors.append('SQL file is placeholder or not a CREATE definition: '+o['path'])
 if re.search(r'\bTODO\b|REPLACE_WITH_LIVE|\<REAL_',s,re.I):
  errors.append('Unresolved placeholder: '+o['path'])
 # GET_DDL often returns quoted names. Check object stem (not type string only).
 if o['name'].split('.')[-1].split('(')[0].upper() not in s.upper():
  errors.append('Object name does not appear in DDL: '+o['path'])
if not (root/'inventory/grants_source.csv').is_file():
 errors.append('Missing source grants snapshot: inventory/grants_source.csv')
if not m.get('source_account_ddl_verified',False):
 errors.append('Operator has not set source_account_ddl_verified to true after independent review')
for w in warnings: print('WARN:',w)
for e in errors: print('BLOCKER:',e)
print(f'RELEASE_GATE={"BLOCKED" if errors else "SOURCE_CODE_CAPTURED_REVIEW_STILL_REQUIRED"}; blockers={len(errors)}; warnings={len(warnings)}')
sys.exit(2 if errors else 0)
