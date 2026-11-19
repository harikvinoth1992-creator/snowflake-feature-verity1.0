# Emergency account-expiry recovery → Git (highest priority)

1. SOURCE account under an authorized role: execute `sql/00_export/00_emergency_backup.sql`; immediately save the full `VERITY_V1_0` and `DE_PIPELINE_POC_DB` database GET_DDL results as UTF-8 `.sql` **outside Snowflake**. Verify the SQL text is not truncated.
2. Capture `SHOW` inventory of schemas/tables/views/semantic views/sequences/functions/procedures/streams/tasks/stages/agents/policies/warehouses/integrations and all role grants/ownership. Export list to `inventory/source_inventory.csv`. **Do not treat an empty SHOW result as proof that the object never existed if your role lacks privileges.**
3. Execute `python scripts/print_export_queries.py`; save each live object's definition to matching path in `sql/**/live/`. For semantic views use `GET_DDL('SEMANTIC_VIEW',...)`; for agent use `GET_DDL('CORTEX_AGENT',...)` using its owning role so its specification is not redacted. `GET_DDL('DATABASE')` may omit account integrations/rights; `SHOW INTEGRATIONS` and `DESCRIBE INTEGRATION` separately.
4. Export all ten framework table records, plus sample/project data where authorized. Put PII/real data in protected raw backup; Git contains approved synthetic fixtures and cleaned code only. DDL alone does NOT save rows or stream offsets.
5. `backup/raw/` (gitignored) preserves untouched full source backups. Do not edit these backups to fit the new account. Keep checksums and backup copies in separate durable storage.
6. Compare live object inventory with all exported definitions; include every discovered object not listed in the initial manifest, including user-defined functions, semantic views, sequences, stages, grants, policies and extra SP signatures.
7. Push to a PRIVATE Git repository; open the remote repository and verify content, latest commit hash and file counts. Store sensitive full raw backup separately. The ZIP generated from this assistant is not a replacement for Git or live DDL export.
8. After source account expiry, rebuild in new empty account using the original fixed names, then harden and test in a separate branch.

## Recovery row-state policy
- **Code/infrastructure:** exact DDL and account settings.
- **Configuration:** source mapping and rule catalog need mapping to new project FQNs and approval provenance; do not bulk copy stale source IDs blindly.
- **History:** profile/run/audit/queue/notification historical rows archived separately, not automatically reseeded in live new account.
- **Stream:** offset cannot be recreated from `GET_DDL`; create stream only after source data is loaded, then establish new baseline; do not replay old approval events inadvertently.
- **Task:** create suspended; only an approved controlled rollout resumes.

## Commit and verify (GitHub browser, no local CLI dependency)
Create a PRIVATE repository, upload cleaned `README.md`, `AGENTS.md`, `config/`, `docs/`, `deploy/`, `scripts/`, `sql/`, `tests/`, `inventory/source_inventory.csv` after review. Confirm expected files are visible in the remote. Do not use `public` while account names, real source data, personal info or DDL might be sensitive. Do not commit role mappings with personal usernames, recipient addresses, tokens or private keys.
