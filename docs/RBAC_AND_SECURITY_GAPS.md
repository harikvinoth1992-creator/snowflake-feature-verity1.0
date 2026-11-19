# RBAC production gates — known gaps from working pilot

- **Temporary pilot workaround** `VERITY_V1_0_EXEC_DE_PIPELINE` got direct `INSERT` on `DQ_RULE_CATALOG`; this can allow insertion of `ACTIVE` rules. Do NOT silently ship it in production role grants.
- Caller-rights `SP_DQ_ONBOARD_TABLE` requires direct `INSERT/UPDATE` on `CONFIG.DQ_SOURCE`, and `INSERT` on `CONFIG.DQ_RULE_CATALOG`; the security boundary needs a controlled owner-rights authorization-scoped redesign and regression tests.
- Owner-rights `SP_DQ_STAGE_AI_RECOMMENDATION` restricts itself to DRAFTs but accepts any enabled `SOURCE_ID`; restrict per project/caller, avoid direct catalog write.
- Owner-rights `SP_DQ_APPROVE_PROFILE_RULE` supports profiled `NO_EDGE_WHITESPACE`, `NOT_BLANK`, `UNIQUE_NORMALIZED`; standard NOT_NULL/UNIQUE/RANGE/VALUE_SET/CONDITIONAL_REQUIRED approval path must be checked independently.
- Shared approval Stream Task can see many projects; task service must validate each source's authorization rather than broad blanket SELECT.
- `SP_DQ_PROCESS_APPROVAL_VALIDATIONS` is caller-rights: queue and Stream read/update rights are needed; grant `SELECT` on underlying approval audit table BEFORE Stream SELECT.
- Grant integration `USAGE` only to the effective role executing `SP_DQ_NOTIFY_DRAFT_RULES`; check its actual `EXECUTE AS` mode. Do not claim delivered emails from `SYSTEM$SEND_EMAIL` accepted status alone.
- Owner of high-privilege procedures currently can be ACCOUNTADMIN. Migrate to scoped owners only with controlled grant and testing.

## RBAC negative tests (dedicated role with USE SECONDARY ROLES NONE)
DE runtime: source SELECT pass; source UPDATE/DELETE fail; catalog status UPDATE fail; inserting ACTIVE rule fail. Steward: SELECT draft and CALL approval pass; direct catalog UPDATE fail; source table write fail. Viewer: read monitoring/results pass, write fail. Task service: manual dispatcher pass for authorized source only, unauthorized project source denied. Admin: deployment permitted only under controlled account admin.

## Deployment policy
Do not run grant script `sql/12_grants/90_pilot_unsafe_grants_DO_NOT_RUN.sql` (reference-only). Apply pilot-dev workaround only under explicit scoped authorization and revoke after redesigned owner-rights intake passes. Release gate requires security signoff.
