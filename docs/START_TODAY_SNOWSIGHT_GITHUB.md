# Start today — highest-priority actions before source account expires

## First: rescue the working implementation (P0, no code changes)

1. Sign in to your **old/source** Snowflake account. Activate an authorized role such as `ACCOUNTADMIN`.
2. In Snowsight, open `sql/00_export/00_emergency_backup.sql` from this package. Run the FIRST TWO `GET_DDL('DATABASE',...)` SELECT statements independently.
3. Copy **the complete SQL text** to separate offline UTF-8 text files `VERITY_V1_0_FULL_DDL.sql` and `DE_PIPELINE_POC_DB_FULL_DDL.sql`. Open and check their beginning and end; Snowsight previews may truncate.
4. Run schema fallbacks if needed. Save the outputs for the 5 Verity schemas, and individually export **every** procedure, view, semantic view, Stream, Task, Agent. `python scripts/print_export_queries.py` prints each source object and destination file path. If the local Python tool doesn't work, read the list in `config/object_manifest.json` and run GET_DDL directly in Snowsight.
5. Run all `SHOW` commands and export object listings; note exact names for any extra semantic view, Cortex Agent, sequence, function, stage, policy. `GET_DDL('CORTEX_AGENT', ...)` must be executed with its owner role to recover the full specification.
6. Back up all required CONFIG, RESULTS, MONITORING and approved project source rows via CSV to protected storage. You can preserve raw history but **must not automatically import that history as live queue/audit events in the new account**.
7. Export grants (to roles, to users, on objects), warehouse properties, integration settings, Task owner/state. Store private identifiers securely.
8. Copy your reviewed DDL into corresponding `sql/**/live/` Git-repository folders. Include other objects discovered in `config/object_manifest.json`. Don't rename table/procedure names or refactor yet.

## Second: save to a PRIVATE GitHub repository (P1)

1. Create private repository `verity-v1.0` (or your approved project name).
2. In GitHub browser, upload the contents of this ZIP's `Verity_V1_0_Git_Deploy_Kit` directory (not ZIP alone). Upload only sanitized SQL/code/documents. Do not upload private emails, secrets, or raw source data.
3. Commit. Verify the private Git URL, branch, commit hash and that `AGENTS.md`, `README.md`, `deploy/INSTALL_ORDER.md`, `config/object_manifest.json`, and live `.sql` files are readable from a different browser session.
4. Retain an untouched full raw DDL backup in separate secure storage; Git is versioned code, not a database data-backup system.

## Third: new account (P2–P4)

1. Confirm different account and availability of Cortex features. Configure users/roles and verified recipient email independently.
2. Run `python scripts/release_gate.py` locally (or instruct deployment agent to run it). Resolve every missing LIVE DDL and inventory issue. If local Python still broken, agent must inspect the manifest manually and refuse deployment while any object missing.
3. Agent opens `AGENTS.md`, obtains permission to deploy, then applies each phase in `deploy/INSTALL_ORDER.md` in Snowsight. The new account must be empty for the destructive/as-built DDL.
4. Validate the two synthetic project fixtures and all six rule types; then test authorized real DE project tables if available. Test steward, Cortex AI, email, post-load, Stream, queue, Task and negative RBAC permissions.
5. Keep Task suspended until its cross-project authorization policy, execution under service role and retry/recovery tests pass.
6. Reconcile source vs target object inventories, row counts, grant lists, SQL definitions. Record signed acceptance evidence; only then claim no missing objects.

## Time-critical fallback
If you run out of time: prioritize **raw database/schema GET_DDL, full procedure DDL and source catalog/rows, grants, Cortex Agent + semantic view definitions, private Git/protected storage verification**. Clean deployment scripts and RBAC hardening can be completed AFTER the old account expires, but missing source definitions may be unrecoverable.
