#!/usr/bin/env python3
"""Print read-only Snowflake GET_DDL statements for all manifest objects."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
m=json.loads((root/'config/object_manifest.json').read_text())
print('-- Run in SOURCE account via Snowsight; save each full DDL result to the matching file.')
for o in m['objects']:
 typ=o['type']
 n=o['name']
 if typ in ('ROLE','NOTIFICATION_INTEGRATION'):
  print(f'-- {n}: capture SHOW / DESCRIBE and GRANTS; email integrations are NOT retrieved with GET_DDL.')
  continue
 print(f"-- {o['path']}  (required={o['required']}; verify existence)")
 print(f"SELECT GET_DDL('{typ}', '{n}', TRUE);")
print('-- INVENTORY DISCOVERY IS ALSO REQUIRED: SHOW SEMANTIC VIEWS; SHOW AGENTS; SHOW FUNCTIONS; SHOW STAGES; SHOW SEQUENCES etc.')
