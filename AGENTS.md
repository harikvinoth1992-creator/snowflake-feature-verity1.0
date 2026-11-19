# Verity V1.0 — Mandatory Instructions for AI Deployment Agents

## Mission
Recover exact live Snowflake definitions from the expiring source account, preserve raw snapshots independently, reconcile inventory and deploy to a NEW, EMPTY target Snowflake account **without dropping, replacing or fabricating source objects**.

## Hard stops: never override
1. Run `python scripts/release_gate.py` and review all blockers. A missing required SQL file, source inventory, missing source object or any unreviewed dependency => STOP. No assertion of 'zero object loss' before postflight reconciliation.
2. Never create guessed DDL to replace a missing stored procedure, semantic view, Cortex Agent, table or integration. Only captured live DDL or explicitly approved new code is allowed.
3. Never run `CREATE OR REPLACE` on an account with existing target objects without a reviewed migration/backup; use the installer only on a new empty account.
4. No task RESUME, email sends, Cortex calls, catalog updates, or source DML without explicit operator approval. Do not copy actual production records into Git.
5. Never permit the runtime role to insert ACTIVE rules or UPDATE rule status directly. Development pilot has **unsafe temporary direct INSERT** on `DQ_RULE_CATALOG`; do not put that in hardened production grants.
6. SOURCE 501 (DE pipeline) and SOURCE 701 (synthetic) are pilot IDs, not stable IDs after restore. Resolve `SOURCE_ID` dynamically from registered FQN.
7. Use Snowsight if the local Snowflake CLI is unavailable. Never claim the CLI or a Git synchronization is functioning without actually verifying it.
8. Never copy an email address, password, token, user mapping, or unsanitized historical logs into public Git.

## Recovery order
First run `sql/00_export/00_emergency_backup.sql`, save raw DDL and CSVs outside Snowflake, compare source catalog to the manifest, recover missing semantic view/agent definitions and grants. Preserve the raw source snapshot unchanged. `GET_DDL('DATABASE', ...)` is a fallback snapshot, not sufficient proof that every object, account integration and row was captured.

## Install order (strict)
See `deploy/INSTALL_ORDER.md` and `deploy/deployment_manifest.json`. Role creation → warehouse/database/schemas → tables/sequences → sample project DBs → regular views → procedures (dependency checked) → stream → suspended task → semantic views → `VERITY_AI_ASSISTANT` → email integration → object grants/ownership → approved source registration/data → read-only checks → authorized functional tests → optional scheduled task resume. Agent referencing a semantic view must be created AFTER the semantic view.

## Agent execution contract
1. Identify environment and confirm target is a separate empty Snowflake account.
2. Read `README.md`, `docs/ARCHITECTURE_DEPLOY.md`, `docs/RECOVERY_AND_GIT.md`, and `deploy/INSTALL_ORDER.md`.
3. Run local gate; publish missing objects with evidence; stop if gate fails.
4. Print ordered SQL plan using `python scripts/print_plan.py`; do not execute any unreviewed SQL.
5. Obtain explicit user permission to perform deployment in new account.
6. Apply each phase in Snowsight as an authorized role. Reconcile live object names and privilege ownership after each phase.
7. Run `tests/ACCEPTANCE_MATRIX.md` / individual SQL checks, capture statuses/query IDs and unexpected behavior. A SQL task `SUCCEEDED` can coexist with a procedure-returned `ERROR`, so validate application JSON separately.
8. Confirm no extra or missing objects, tasks suspended unless approved, grants verified and role negative tests passed. Complete `release/EVIDENCE_AND_SIGNOFF.md` before reporting completion.

## Known blocker
The repository contains reference SQL and an offline installer plan, **but is not a deployable recovery of live Verity until the operator adds actual captured object DDL and inventory**. Do not hide that fact.

## Config-driven deployment contract
- First copy `config/verity.example.yaml` to ignored `config/verity.local.yaml` (or use ignored `.json` copy of the example JSON). Map local account USERS/ROLES; no hardcoded individual identity is deployable.
- Run `python scripts/render_config.py --config config/verity.local.yaml` (requires PyYAML) or `--config config/verity.local.json` (stdlib-only), then inspect `deploy/generated/deployment_manifest.configured.json` with `python scripts/print_plan.py --manifest deploy/generated/deployment_manifest.configured.json`.
- Use `deploy/generated/` SQL for phases 01, 02, 12 rather than the hardcoded example scripts; generated user-role grants require explicit account-admin authorization. `deploy/generated/` is deliberately gitignored as environment-specific output.
- `project_sources.approved` must be explicitly set true for each permitted table. No blanket future grants. A commenter setting `approved` true is not actual evidence of project owner approval; capture signoff.
- The renderer deliberately BLOCKS arbitrary database or warehouse naming, since the real Verity V1 procedures hardcode them. Do not claim config values drive all procedure/Task/agent integration settings. Capture and review exact DDL first.
- Integration grant file is comment-only pending notifier EXECUTE AS review; don't uncomment automatically. Tasks never start on install.

## v3 template rendering contract

- Render `sql/templates/**/*.sql.j2` into `deploy/generated/` with `scripts/render_config.py`; never execute `{{ ... }}` templates as raw Snowflake SQL.
- Opt-in `bootstrap.grant_admin_to_current_user` generates `CURRENT_USER()` ADMIN self-grant. The bootstrap user inherits RUNTIME through ADMIN role hierarchy but is not automatically granted STEWARD, VIEWER or internal TASK_EXEC.
- The `SYSADMIN` hierarchy grant is explicitly configured. Do not create any cycle or assign task service to personal accounts.
- Template renderer is allowlist-based with strict identifier validation; do not change it to unsafe arbitrary eval or search-and-replace on entire quoted procedure bodies.
- Live DDL and inventory remain critical release blockers; source exports must be verified and backed up separately.

