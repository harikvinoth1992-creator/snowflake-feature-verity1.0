# Strict deployment runbook — New, empty Snowflake account only

**Environment approval:** account identity/region, source-vs-destination, warehouse budget, Cortex model availability, verified email recipients, project-owner approvals. Log operator, timestamp, Snowflake query IDs in `release/EVIDENCE_AND_SIGNOFF.md`. Keep all Tasks SUSPENDED.

| Phase | SQL/assets | Must be true before next phase | Who runs |
|---|---|---|---|
| 00 | `sql/00_export/` | **Only SOURCE account:** DDL + object/data/grant inventory backed up and compared | Account admin |
| 01 | `sql/01_roles/01_create_roles.sql` | Five roles created; no direct user grants except approved mappings | SECURITYADMIN |
| 02 | `sql/02_infrastructure/01_database_warehouse_schemas.sql` | Warehouse/database/schemas present | Deployment admin |
| 03 | `sql/03_tables/live/*.sql` and sequences | All ten known tables, column types, defaults, identity/keys match live DDL; reconcile other discovered objects | Object owner |
| 04 | `sql/04_sample_projects/` | Synthetic project A/B fixtures; real DE table restored only if source DDL and data approved | Project owner |
| 05 | `sql/05_views/live/*.sql` | `MONITORING.V_DQ_PROFILE_EVIDENCE` available | Object owner |
| 06 | `sql/06_procedures/live/*.sql` excluding dispatcher | Exact signatures, nested rights, owner and dependency verified; deploy leaf dependencies first | Object owner |
| 07 | `sql/07_streams/live/*.sql`, then dispatcher `sql/06_procedures/live/SP_DQ_PROCESS_APPROVAL_VALIDATIONS.sql` | Approval audit exists; stream created *after* chosen data restoration and activation baseline (stream offset not portable) | Object owner |
| 08 | `sql/08_tasks/live/*.sql` | Dispatcher exists; Task created SUSPENDED; do not resume | Task role admin |
| 09 | `sql/09_semantic_views/live/*.sql` | All discovered semantic views restored and verified | Object owner |
| 10 | `sql/10_agents/live/*.sql` | `VERITY_AI_ASSISTANT` restored if actually present, connected to existing semantic view | Agent owner |
| 11 | `sql/11_notifications/` | Email integration name/allowed recipients verified; no unreviewed send | Account admin |
| 12 | `sql/12_grants/` | Grants applied by required owner/authorized grant manager; task owner separately transferred/created as service role | Security & admin |
| 13 | `sql/13_seed/` | Sanitized demo data, approved source records; **do not import old queue/stream/history as live** | Data owner |
| 14 | `sql/14_validation/` | Six DQ types, AI, steward, notification, post-load, RBAC negative tests passed | Test roles |
| 15 | `sql/15_activate/` | Explicit opt-in and cross-project source allowlist verified before Task RESUME | Task owner |
| 16 | `sql/16_reconcile/` | No missing original objects, row counts/DDL/grants compare, release evidence signed | Release manager |

**Important dependency details:** Base profiling evidence views belong before callers; semantic view is a later reporting/agent dependency. Email integration can be provisioned earlier, but is validated in phase 11 and its USAGE grants applied in phase 12. `CREATE OR REPLACE` may delete old objects or reset Streams, so use this procedure **only on fresh target**. Maintain separate upgrade strategy.

### Procedure order (verify references from exact GET_DDL before execution)
1. `SP_DQ_ONBOARD_TABLE` and `SP_DQ_PROFILE_TABLE`.
2. `SP_DQ_STAGE_AI_RECOMMENDATION` (dependency of deterministic/AI intake).
3. `SP_DQ_AUTO_STAGE_PROFILE_DRAFTS`, `SP_DQ_GENERATE_AI_RECOMMENDATIONS`.
4. `SP_DQ_NOTIFY_DRAFT_RULES`, `SP_DQ_APPROVE_PROFILE_RULE`, `SP_DQ_EXECUTE_HYBRID_V1_0`.
5. Optional `SP_DQ_ONBOARD_AND_NOTIFY`, then `SP_DQ_ONBOARD_AND_NOTIFY_AI`, `SP_DQ_POST_LOAD_VALIDATE`.
6. Create approval audit Stream (phase 07) **before** `SP_DQ_PROCESS_APPROVAL_VALIDATIONS` if compilation requires it; move dispatcher last in phase 07/08 as a documented dependency exception.
7. Create suspended Task referencing the dispatcher.

**If object dependencies demand a different ordering:** document the change in manifest before executing; never silently omit an object.

### SQL deployment detail
`python scripts/print_plan.py` produces a text order and missing SQL paths. Each live SQL file must be the verified Snowsight GET_DDL output for that object, reviewed and sanitized, not a placeholder. We deliberately do not auto-execute Snowflake SQL here: no working CLI was established in the source environment and agent deployment requires an explicit approval. An authorized agent may execute reviewed statements via Snowsight / supported connection only after the release gate passes.

### Parameterized operator path (NEW)
Run `python scripts/render_config.py --config config/verity.local.json` for the
stdlib-only deployment option; YAML works if PyYAML is installed. This creates
`deploy/generated/deployment_manifest.configured.json`.
For phases **01 / 02 / 12**, use the files listed in the generated manifest,
not hardcoded examples. Phase 12 user-role assignments must be executed only
after the Snowflake user accounts exist and the admin approves the mapping.
The generated integration script is **review-only**; it cannot send email or
unconditionally grant email integration access. Other phases still point to the
exact live-object DDL recovered from the source account. Keep Task SUSPENDED.

### v3 account-independent role bootstrap

`sql/templates/01_roles/{01_create_roles,02_role_hierarchy_and_bootstrap}.sql.j2` render to two separate Phase 01 SQL files. The second file includes `GRANT ROLE {{ runtime_role }} TO ROLE {{ admin_role }}`, `GRANT ROLE {{ admin_role }} TO ROLE SYSADMIN`, and optional `SET VERITY_USER = (SELECT CURRENT_USER()); GRANT ROLE {{ admin_role }} TO USER IDENTIFIER($VERITY_USER);`. All are generated from `config/verity.local.yaml` / `.json`, validated, then reviewed. Run under `SECURITYADMIN` or equivalent. **Do not grant steward approval through an inherited runtime role.**
