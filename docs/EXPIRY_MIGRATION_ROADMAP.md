# Verity V1.0 — Expiring Snowflake Account Recovery and Git-to-New-Account Roadmap

**Prepared:** 2026-11-19  
**Primary objective:** preserve the real live implementation before expiry, then prove an independent clean-account deployment.  
**Source environment:** `VERITY_V1_0` framework, `DE_PIPELINE_POC_DB` project POC.  
**Important:** This is a migration plan, NOT proof that the current code has already been backed up or made portable.

## Release gates (in strict priority order)

- [ ] **P0: Source recovery captured outside Snowflake** — full DDL, account metadata, configuration and approved sample data downloaded; backup readable after logout.
- [ ] **P1: Git backup verified** — private repository with raw recovery snapshot and a separate cleaned deployment tree; commit confirmed in GitHub browser.
- [ ] **P2: Installer prepared** — YAML-driven account/project mappings, ordered SQL, idempotent or documented rerun behavior, no secrets in Git.
- [ ] **P3: Clean new-account deployment** — framework and POC source recreated with least-privilege roles.
- [ ] **P4: Acceptance passed** — six mandatory DQ rules, AI suggestions, steward approval, notifications, post-load validation, scheduled queue, negative RBAC tests.
- [ ] **P5: Production controls** — restricted owner-rights intake, scope enforcement, cost controls, recovery/retry procedures, release notes and signoff.

## P0 — Rescue from original account now

### A. Snapshot database object DDL (database GET_DDL is recursive)

```sql
USE ROLE ACCOUNTADMIN;
SELECT GET_DDL('DATABASE', 'VERITY_V1_0', TRUE) AS VERITY_COMPLETE_DDL;
SELECT GET_DDL('DATABASE', 'DE_PIPELINE_POC_DB', TRUE) AS PROJECT_POC_DDL;
```

Store the full text **as SQL**, not only a CSV with a single escaped SQL cell. If the full output is too large or truncated, split by schema:

```sql
SELECT GET_DDL('SCHEMA', 'VERITY_V1_0.CONFIG', TRUE);
SELECT GET_DDL('SCHEMA', 'VERITY_V1_0.ENGINE', TRUE);
SELECT GET_DDL('SCHEMA', 'VERITY_V1_0.RESULTS', TRUE);
SELECT GET_DDL('SCHEMA', 'VERITY_V1_0.MONITORING', TRUE);
SELECT GET_DDL('SCHEMA', 'VERITY_V1_0.PRACTICE', TRUE);
```

Check object inventory before and after export:

```sql
SHOW SCHEMAS IN DATABASE VERITY_V1_0;
SHOW TABLES IN DATABASE VERITY_V1_0;
SHOW PROCEDURES IN SCHEMA VERITY_V1_0.ENGINE;
SHOW VIEWS IN DATABASE VERITY_V1_0;
SHOW STREAMS IN DATABASE VERITY_V1_0;
SHOW TASKS IN SCHEMA VERITY_V1_0.ENGINE;
SHOW WAREHOUSES LIKE 'VERITY_V1_0_WH';
SELECT GET_DDL('WAREHOUSE', 'VERITY_V1_0_WH');
```

Also inspect semantic views and any stages/sequences/UDFs/data metric functions not obvious in the main list; keep any custom policies and referenced objects. Save worksheet source and query-history snippets that are absent from live objects.

### B. Capture account objects and grants

```sql
SHOW ROLES LIKE 'VERITY_V1_0%';
SHOW GRANTS TO ROLE VERITY_V1_0_ADMIN;
SHOW GRANTS TO ROLE VERITY_V1_0_EXEC_DE_PIPELINE;
SHOW GRANTS TO ROLE VERITY_V1_0_STEWARD;
SHOW GRANTS TO ROLE VERITY_V1_0_VIEWER;
SHOW GRANTS TO ROLE VERITY_V1_0_TASK_EXEC;
SHOW GRANTS OF ROLE VERITY_V1_0_EXEC_DE_PIPELINE;
SHOW GRANTS ON TASK VERITY_V1_0.ENGINE.TK_DQ_VALIDATE_APPROVED_RULES;
SHOW FUTURE GRANTS IN DATABASE VERITY_V1_0;
SHOW INTEGRATIONS;
```

For actual notification integration name, save `DESCRIBE INTEGRATION <VERIFIED_NAME>;`. Document verified recipient restrictions and email integration creation details separately; keep account-specific identifiers and any secrets out of Git. Capture warehouse auto-suspend, size, task schedule/state, task owner, execute-task account grant, Cortex entitlement/model availability, and role grants to users (template instead of personal names).

### C. Preserve state/data separately from object DDL

Export approved CSVs or protected snapshots for:
- `CONFIG.DQ_SOURCE`, `CONFIG.DQ_RULE_CATALOG`
- `MONITORING.DQ_METRIC_HISTORY`
- `RESULTS.DQ_RUN`, `RESULTS.DQ_RULE_RESULT`, `RESULTS.DQ_POST_LOAD_RUN`
- `RESULTS.DQ_RULE_APPROVAL_AUDIT`, `RESULTS.DQ_APPROVAL_VALIDATION_QUEUE`
- `RESULTS.DQ_RULE_NOTIFICATION_LOG`, `RESULTS.DQ_VALIDATION_RECOVERY_AUDIT`
- Required `PRACTICE` sample tables and `DE_PIPELINE_POC_DB.LAB.ORDER_FULFILMENT`, optionally `INVENTORY_ALERTS`

**Keep historical audit/queue/result data as archive, not automatically live seed.** On fresh install seed only intentional configuration/test data; start streams and queues clean, or deliberately reconcile restored events. Validate identity columns, timestamps, primary keys, sequences, dependency order, and sensitive data handling before import.

### D. Verify backups

- [ ] Full `VERITY_V1_0` DDL downloaded and readable.
- [ ] Project POC DDL downloaded and readable.
- [ ] Each procedure from `SHOW PROCEDURES` appears in the backup.
- [ ] All views, semantic views, streams, tasks, tables, functions, sequences and relevant integrations are accounted for.
- [ ] Live data/config CSVs backed up outside account.
- [ ] Roles, grants, account-level configuration recorded.
- [ ] Files uploaded to a private Git repository (code and sanitized seed only) or a separate protected durable location (sensitive raw exports).

## P1 — Repository structure and preservation

```text
verity-v1.0/
  README.md
  docs/
    MIGRATION_ROADMAP.md
    ARCHITECTURE.md
    OBJECT_INVENTORY.md
    RBAC_MATRIX.md
    TEST_EVIDENCE.md
    RELEASE_NOTES.md
  backup/
    raw/                      # sanitized recovery DDL; restrict sensitive material
  config/
    verity.example.yaml
    projects.example.yaml
  sql/
    00_bootstrap/             # account prerequisites, roles, warehouse, schemas
    01_tables/                # framework tables and sequences
    02_views/                 # evidence and semantic views
    03_procedures/            # all engine procedures, ordered
    04_streams/               # stream after audit table
    05_tasks/                 # create suspended, configure after grants
    06_grants/                # account, object, project, steward, service roles
    07_seed/                  # sanitized demo data and catalog configuration
    08_verification/          # read-only inventory and E2E SQL
    09_rollback/              # controlled cleanup/recovery
  tests/
    01_deploy_smoke.sql
    02_dq_six_rules.sql
    03_ai_recommendations.sql
    04_steward_approval.sql
    05_post_load.sql
    06_task_manual.sql
    07_rbac_negative.sql
    08_cost_baseline.sql
  deploy/
    INSTALL_ORDER.md
    preflight.sql
    postflight.sql
  .gitignore
```

Save first intact *raw* DDL, then split into files. Never destroy the only full snapshot while refactoring.

## P2 — Clean-account deploy design

Recommended configuration fields: `connection`, `db`, `wh`, `wh_size`, `admin_role`, `runtime_role`, `viewer_role`, `steward_role`, `task_role`, `project_database`, `project_schema`, `approved_source_tables`, `notification_integration`, `steward_email`, `cortex_model`, `enable_scheduled_task=false`, and role-to-user assignments. Commit examples only, not actual credentials or personal email addresses.

The current code contains hardcoded `VERITY_V1_0` references; a YAML file by itself does **not** parameterize those procedure bodies. Implement and test a token replacement/generation step, or preserve the fixed database name in release 1 with an explicit documented limitation. Do not claim arbitrary renamed-database deployments work until tested.

Recommended setup order:
1. Account/region/features preflight (roles, warehouse, Cortex model access, email recipient constraints).
2. Roles and warehouse, framework database and schemas.
3. Tables and sequences, then base source-project schema/demo tables.
4. Views/evidence and optional semantic views, accounting for dependencies.
5. Procedures in nested dependency order; `EXECUTE AS` and privilege ownership verified.
6. Approval audit stream after its table; create Task suspended.
7. Grant database/schema/table/procedure/integration/stream access and Task account privilege; assign controlled role owners.
8. Seed sanitized rules/sources/demo data without manufacturing audit history; initialize streams carefully.
9. Run smoke tests, then optional manual Task execution.
10. Resume the Task only after cross-project authorization has been verified and the user/operator explicitly enables it.

## P3 — New Snowflake account steps

- [ ] Record account locator, region and edition; verify supported Cortex models/privileges and notification integration setup.
- [ ] Provision account administrator and new account users/service mappings (no hardcoded `HARIVINOTH` role assignment).
- [ ] Deploy roles `ADMIN`, `EXEC_DE_PIPELINE`, `STEWARD`, `VIEWER`, and internal `TASK_EXEC` (use actual role spelling `VERITY_V1_0_STEWARD`).
- [ ] Create warehouse with small size, auto-suspend and cost alert/resource monitor as permitted.
- [ ] Run SQL deploy files in documented order; verify all objects and dependent procedures.
- [ ] Configure and test email integration with verified permitted recipients.
- [ ] Load only sanitized test data and approved source registrations.
- [ ] Verify all grants with secondary roles OFF; independently test each role.
- [ ] Keep Task suspended until the shared-queue security tests pass.

## P4 — Acceptance matrix (record query ID and actual response)

| Test | Expected proof |
|---|---|
| Cross-project onboarding | DE project table read with narrow SELECT, source registered |
| Profiler | TEXT, NUMERIC, DATE/TIMESTAMP, keys: null, blank, edge whitespace, min/max, distinct evidence |
| Standard DQ rules | NOT_NULL, UNIQUE, RANGE, VALUE_SET, CONDITIONAL_REQUIRED, NO_EDGE_WHITESPACE |
| Cortex | Evidence-based DRAFT or explicit NO_ELIGIBLE_CANDIDATES; model credit and errors tracked |
| Deterministic drafts | Draft status, evidence, no direct activation |
| Human governance | Steward approval allowed; runtime direct UPDATE/ACTIVE insertion denied; audit ACTIVATED |
| Notification | Verified recipient, integration grant, log row, email accepted; delivery checked separately |
| Hybrid run | DQ_RUN and DQ_RULE_RESULT written; DONE or DONE_WITH_DQ_FAILURES correctly interpreted |
| Post-load | unique load ID idempotence, profile+validate, history recorded |
| Approval Stream/queue | Capture, batch, retries/dead handling, audit, manual TASK_EXEC run |
| Scheduled Task | owner TASK_EXEC, explicit opt-in schedule, history SUCCESS, authorized sources only |
| Viewer | SELECT works, writes denied |
| DE runtime | source SELECT works, source INSERT/UPDATE/DELETE denied |
| Second project | independent schema/project access and no unauthorized cross-access |
| Idempotent installer | repeat install / upgrade handled without losing existing data or replacing running objects |
| Costs | warehouse/Cortex baseline and guardrails |

## P5 — Known hardening work; do not treat as completed

1. `SP_DQ_ONBOARD_TABLE` is caller's-rights and currently needs direct `INSERT` on `DQ_RULE_CATALOG` and `INSERT, UPDATE` on `DQ_SOURCE`: development workaround permits bypassing DRAFT/approval controls. Design controlled owner-rights gateway and source allowlist before production; only then revoke direct writes.
2. `SP_DQ_STAGE_AI_RECOMMENDATION` is owner's-rights and restricts insertion to DRAFT with evidence but needs per-caller/per-project source authorization and concurrency-safe exact rule ID auditing.
3. `SP_DQ_APPROVE_PROFILE_RULE` is owner's-rights, supports only its three profiled rule types and is not the same as general approval for six standard rules; verify all needed governance paths.
4. Shared `SP_DQ_PROCESS_APPROVAL_VALIDATIONS` processes events from all sources but service role currently has tested access to DE 501 and synthetic 701 only. Implement source scope/least privilege for future projects before unattended resumption.
5. Audit stale queue `PROCESSING` recovery, retries, stream offset handling and idempotent post-load behavior.
6. Consider high-privilege procedure ownership migration carefully; record current owners before altering them.
7. Template hardcoded object names in all procedure/view/task definitions and validate installation from clean account.
8. Source project test tables currently synthetic/POC; add independent second project for full two-project design acceptance if not already present.
9. Ensure `REGEX` is not substituted for any required rule; six required rule types are acceptance baseline.
10. Cost, Cortex permission, email integration, object ownership, and scheduled task state are account-specific and need repeat verification.

## Failure recovery

If expiry occurs early: rely on downloaded raw DDL, protected CSVs and Git commit. Deploy the original fixed-name DDL first if necessary; defer refactoring and optional features. A source account inaccessible after expiry cannot be assumed recoverable. Do not rely on Snowflake worksheets or old query history as the only backup.

**Release definition of done:** all inventory objects reconciled, sanitized source/state reproducible, a clean account installs successfully, role segregation tested, all mandatory flows validated, cost/scheduler limits configured, and deployment instructions are repeatable by another user.
