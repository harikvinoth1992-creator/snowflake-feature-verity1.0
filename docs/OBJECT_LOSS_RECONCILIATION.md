# Object-loss prevention and post-deploy reconciliation

## Capture facts first
For SOURCE and TARGET record separately: exact `SHOW` inventories, DDL SHA256, role owners, dependent grant matrix, table counts and any required sequence/identity state. Include account-level objects (warehouse, integration, roles) outside the database.

## Compare all categories
1. Databases, schemas, tables and **all column definitions** (types/defaults/nullability).
2. Views, semantic views and their dependencies.
3. Stored procedures: exact name, overload signature, body hash, `EXECUTE AS` context, owner.
4. Streams and source table, Task schedule/state/owner/SQL, any alerts/DMFs/functions/stages/sequences/policies/tags discovered by `SHOW`.
5. `VERITY_AI_ASSISTANT`: owner-role `GET_DDL('CORTEX_AGENT', ...)` specification and tool references, or mark ABSENT and remove from required list only with evidence.
6. Email integration settings (excluding secrets), permitted verified recipients, integration grants.
7. Role grants incl. warehouse, table, procedure, Task `EXECUTE TASK`, source SELECT, negative controls.
8. Protected historical rows and configuration restored according to declared policy; compare row counts and checksums where meaningful. Historical queue/stream offsets are **not** portable.

## Hard gate
A missing extra source object (not in previous design) is still a **blocker**, not a permitted omission. Update manifest to include it. Fresh account object creation cannot prove 'without loss' until post-deploy inventories match, data migration policy is reconciled, tests pass and exceptions signed.

## Risk controls
- Stop if original source account is no longer available and source DDL missing; report limited recovery instead of inventing SQL.
- Do not copy all `RESULTS` rows into active queues; restore archived results to separate protected archival tables if required.
- Do not use `CREATE OR REPLACE DATABASE` for installation or upgrade.
- Re-run clean-account deployment only after checking idempotence; `CREATE OR REPLACE` on live tables/tasks/streams risks data or offsets.
