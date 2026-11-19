# Verity V1.0 — Source-Recovery to Clean Snowflake Account Git Deployment

**State: SOURCE DDL STILL NEEDS TO BE EXPORTED.** This repo is a structured, offline-checked deployment kit, not a claimed copy of your live Snowflake account. It retains previous project documents in `legacy_reference/` for traceability.

## Start here while your account still exists

1. In the SOURCE account, run `sql/00_export/00_emergency_backup.sql` via Snowsight. Save full `VERITY_V1_0` and `DE_PIPELINE_POC_DB` DDL **outside the account**, plus all live object `SHOW` inventories and approved data.
2. Run `python scripts/print_export_queries.py` to get individually scoped `GET_DDL` statements for each known object. Export actual DDL into matching paths in `sql/**/live/`. These paths are deliberately absent until the real code is supplied.
3. Run `python scripts/release_gate.py`. It reports missing exact object definitions and source inventory; **the default result is BLOCKED**.
4. Commit reviewed SQL and documentation to a PRIVATE Git repo. Backup raw sensitive snapshots to a separate protected location and verify both copies independently.
5. In the NEW empty account, follow `deploy/INSTALL_ORDER.md` and `AGENTS.md`. No automatic task scheduling or source modification.
6. Execute `tests/ACCEPTANCE_MATRIX.md` and capture evidence before calling deployment complete.

## Exact order

`00 export → 01 roles → 02 infrastructure → 03 tables → 04 sample projects → 05 views → 06 procedures → 07 stream → 08 suspended task → 09 semantic views → 10 Cortex Agent VERITY_AI_ASSISTANT → 11 email integration → 12 grants/ownership → 13 seed → 14 validation → 15 optional activation → 16 reconciliation`

We use this precise dependency order rather than assuming all views can be created after procedures: `V_DQ_PROFILE_EVIDENCE` is used by deterministic and AI procedures. The semantic reporting layer can come after the core procedures, but must precede an agent referencing it.

## Project RBAC

Five technical roles: Admin, DE Project Runtime, Steward, Viewer, and **internal** Task Service. Task Service is not a new business-facing role. All project source grants are per approved table. Data Steward approves via `SP_DQ_APPROVE_PROFILE_RULE` (owner's rights), never direct `UPDATE`.

## Tooling

Python 3 standard library only for offline plan/gates. SQL runs in Snowsight in phase order (compatible with the current local Snowflake CLI constraint). The existing earlier Python/CoCo scripts are preserved as `legacy_reference/`; do not treat them as automatically verified target installers.

## Configuration boundaries

Release 1 assumes the exact database `VERITY_V1_0` and warehouse `VERITY_V1_0_WH`; existing procedures hardcode those identifiers. `config/verity.example.yaml` is configuration documentation, **not an SQL template engine**. Do not promise arbitrary renaming until code substitution and clean deployment testing exist.

## Security / data handling

The historic pilot used temporary direct `INSERT` on `CONFIG.DQ_RULE_CATALOG` and `INSERT/UPDATE` on `CONFIG.DQ_SOURCE` for caller-rights onboarding. These grants are unacceptable for production governance. Export the original code first; then harden an authorization-scoped owner's-rights gateway and test before removing temporary grants. The secure install gate should remain blocked if this is unresolved.

## Files

- [`AGENTS.md`](AGENTS.md): mandatory autonomous agent policy.
- [`deploy/INSTALL_ORDER.md`](deploy/INSTALL_ORDER.md): all phase files / stop conditions.
- [`docs/ARCHITECTURE_DEPLOY.md`](docs/ARCHITECTURE_DEPLOY.md): object architecture and data flows.
- [`docs/RECOVERY_AND_GIT.md`](docs/RECOVERY_AND_GIT.md): account-expiry backup instructions.
- [`tests/ACCEPTANCE_MATRIX.md`](tests/ACCEPTANCE_MATRIX.md): test plan.
- [`docs/OBJECT_LOSS_RECONCILIATION.md`](docs/OBJECT_LOSS_RECONCILIATION.md): name/count/definition/row reconciliation.

## Commands

```bash
python scripts/print_plan.py
python scripts/print_export_queries.py
python scripts/release_gate.py
python -m unittest discover -s tests/python -v
```

**Git example:** `git init && git add . && git commit -m "Verity V1 migration backup and deployment runbook"`; then create a private remote and push. The commands do not push files by themselves.

## Working user/role/source parameterization (updated kit)

**NEW:** `scripts/render_config.py` converts the editable `config/verity.example.yaml`
(or equivalent `config/verity.deployment.example.json`) into real SQL in
`deploy/generated/` for roles, warehouse setup, reviewed grant templates,
**approved project-source** access, and `GRANT ROLE ... TO USER ...` statements.

1. Copy `config/verity.example.yaml` to `config/verity.local.yaml` and edit
   `role_assignments.admin_users`, `runtime_de_users`, `steward_users`,
   `viewer_users` with **target account usernames**. For no-PyYAML environments,
   copy `config/verity.deployment.example.json` to `config/verity.local.json`.
2. Set individual `project_sources[].approved: true` only after owner approval.
3. Run **one of**:

   ```bash
   python scripts/render_config.py --config config/verity.local.yaml
   python scripts/render_config.py --config config/verity.local.json
   ```

   YAML requires `PyYAML`; the JSON option uses Python standard library only.
4. Review `deploy/generated/12_grants/08_assign_roles_to_users.sql`,
   `02_project_approved_sources.sql` and the generated integration review.
5. Inspect the parameterized installation plan:

   ```bash
   python scripts/print_plan.py --manifest deploy/generated/deployment_manifest.configured.json
   ```

**Boundaries:** V1 still requires `VERITY_V1_0` and `VERITY_V1_0_WH` due to exact
live DDL references; the renderer deliberately rejects other names instead of
silently breaking deployment. **Cortex model, semantic agent, email integration,
Task schedule and connections are captured in config but require verification
and actual live DDL before installation; they are not magically substituted.**
The renderer creates SQL files only; it never connects, grants, sends emails,
resumes a Task or makes any Snowflake changes. Do not run the base hardcoded
role/grant scripts instead of rendered ones if you chose custom role names.
Source DDL capture and production RBAC hardening remain release blockers.

## Direct SQL-template parameterization (v3)

The Git templates in `sql/templates/` now use **`{{ runtime_role }}` / `{{ admin_role }}`** placeholders like the requested bootstrap pattern. `scripts/render_config.py` resolves them into `deploy/generated/01_roles/` and `deploy/generated/02_infrastructure/`. Set `bootstrap.grant_admin_to_current_user: true` in your local YAML or JSON **only when approved** to generate the `CURRENT_USER()` self-grant. See [`docs/CONFIG_PARAMETERIZATION.md`](docs/CONFIG_PARAMETERIZATION.md). The temporary role grant is never applied automatically: rendering is local only and SQL runs only after operator review.

