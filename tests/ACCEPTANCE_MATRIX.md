# Clean-account acceptance tests: capture query IDs, JSON and role per case

| Test | Executing role | Expected proof |
|---|---|---|
| A01 object inventory | ADMIN | source vs target objects/signatures/grants match; no missing objects |
| A02 DE project source | EXEC_DE_PIPELINE | SELECT approved project table; source UPDATE/DELETE denied |
| A03 onboarding | EXEC_DE_PIPELINE | source registration; only approved table, structured; no direct ACTIVE rule insertion |
| A04 TEXT profiling | EXEC_DE_PIPELINE | null, blank, edge spaces, min/max, distinct captured |
| A05 NUMERIC profiling | EXEC_DE_PIPELINE | min/max, null, negative/outlier evidence |
| A06 DATE/TIMESTAMP profiling | EXEC_DE_PIPELINE | min/max/date/null evidence |
| A07 six standard rules | EXEC_DE_PIPELINE | NOT_NULL, UNIQUE, RANGE, VALUE_SET, CONDITIONAL_REQUIRED, NO_EDGE_WHITESPACE each execute and report expected failures |
| A08 Cortex proposal | EXEC_DE_PIPELINE | AI called only if eligible; DRAFTs require approval; check credits |
| A09 Deterministic proposals | EXEC_DE_PIPELINE | NO_EDGE_WHITESPACE proposal from profile evidence and DRAFT_CREATED audit |
| A10 Steward | STEWARD | owner-rights approval, ACTIVE + ACTIVATED audit; invalid rule REJECTED; direct UPDATE denied |
| A11 Notifications | EXEC_DE_PIPELINE | integration allowed, log records, successful request and separate inbox verification |
| A12 Hybrid | EXEC_DE_PIPELINE | DQ_RUN and DQ_RULE_RESULT persisted; status DONE or DONE_WITH_DQ_FAILURES |
| A13 Post-load | EXEC_DE_PIPELINE | same external load ID does not double-run; new load ID reprofiles/revalidates |
| A14 Stream approval queue | TASK_EXEC | approval Stream consumed once, queue DONE/retry/dead behavior |
| A15 Manual task | TASK_EXEC | EXECUTE TASK ... AWAIT SUCCEEDED AND dispatcher JSON healthy |
| A16 Auto schedule | TASK_EXEC | 1-min schedule only if owner opted in, history succeeded, no unauthorized sources |
| A17 Viewer | VIEWER | reads results; update/insert/delete denied |
| A18 Second project | second approved runtime | independent DB/schema/table; no cross-project source access |
| A19 Semantic view | VIEWER/appropriate analyst | expected metric SQL and permissions confirmed |
| A20 Agent | authorized Cortex Agent user | actual deployed agent reaches semantic view; compare response to SQL |
| A21 Cost | ACCOUNT admin | warehouse credits + Cortex usage recorded; bounded cost config |
| A22 Repair/retry | TASK_EXEC | stale PROCESSING, retries/dead and no lost events under fault injection |
| A23 Idempotence | deploy admin | safe rerun, ownership/grants retained, data not overwritten |

**Do not mark PASS** when procedure was merely callable. Use concrete source ID, rule ID, run ID, query ID, timestamp, expected-vs-actual, screenshot or output reference. `DONE_WITH_DQ_FAILURES` means the DQ engine worked but sample data violated rules. Task `SUCCEEDED` alone does not prove application-level DONE.

## Execution order
1. `sql/14_validation/01_read_only_smoke.sql`; 2. `sql/14_validation/02_six_rule_fixture_checks.sql`; 3. `sql/14_validation/03_integrated_call_templates.sql` (manual authorization required); 4. `sql/14_validation/04_security_negative_templates.sql` (intentional SQL errors); 5. optional task and agent/email tests after prerequisites; 6. reconciliation.
