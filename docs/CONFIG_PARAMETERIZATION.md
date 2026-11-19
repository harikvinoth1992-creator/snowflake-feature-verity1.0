# Parameterized SQL deployment — v3

## The agreed pattern
Write source-controlled SQL as templates under `sql/templates/` with `{{ admin_role }}`, `{{ runtime_role }}`, `{{ warehouse }}` etc. These are **not Snowflake SQL syntax** and MUST be rendered before execution. The local Python renderer supports a small explicit placeholder allowlist rather than full Jinja execution, and strictly validates identifiers. No network, Snowflake login, or secrets are required.

```sql
-- sql/templates/01_roles/02_role_hierarchy_and_bootstrap.sql.j2
USE ROLE SECURITYADMIN;
GRANT ROLE {{ runtime_role }} TO ROLE {{ admin_role }};
GRANT ROLE {{ admin_role }} TO ROLE SYSADMIN;
SET VERITY_USER = (SELECT CURRENT_USER());
GRANT ROLE {{ admin_role }} TO USER IDENTIFIER($VERITY_USER);
```

The generated file includes the CURRENT_USER() self-grant **only if** `bootstrap.grant_admin_to_current_user: true` is explicitly set in the local config. The runtime-under-admin and admin-under-SYSADMIN grants are controlled by corresponding flags. This gives the operator ADMIN and inherited RUNTIME, **not STEWARD or VIEWER**. A non-admin user receives roles from `role_assignments`. The Task service role is NEVER directly granted to users by the renderer.

## Edit once per Snowflake account

```yaml
# config/verity.local.yaml (ignored by Git)
database: VERITY_V1_0
warehouse: VERITY_V1_0_WH
roles:
  admin: CLIENT_VERITY_ADMIN
  runtime_project_de: CLIENT_VERITY_RUNTIME
  steward: CLIENT_VERITY_STEWARD
  viewer: CLIENT_VERITY_VIEWER
  task_service: CLIENT_VERITY_TASK_EXEC
bootstrap:
  grant_admin_to_current_user: true
  runtime_under_admin: true
  admin_under_sysadmin: true
role_assignments:
  admin_users: []
  runtime_de_users: [CLIENT_ETL_USER]
  steward_users: [CLIENT_STEWARD]
  viewer_users: [CLIENT_ANALYST]
```

Copy the entire bundled example file rather than replacing it with the partial example above. See `config/verity.example.yaml` for project source allowlists, warehouse size, Cortex model, notification integration, and scheduling settings.

Render:

```bash
python scripts/render_config.py --config config/verity.local.json
python scripts/print_plan.py --manifest deploy/generated/deployment_manifest.configured.json
```

YAML is supported if PyYAML is installed; `.json` is standard-library only. Review generated SQL under `deploy/generated/` then run appropriate phases under authorized Snowflake roles. **Do not submit Jinja placeholders to Snowsight.**

## Important boundaries

- V1 still requires database `VERITY_V1_0` and warehouse `VERITY_V1_0_WH` until the hardcoded live DDL is captured, parameterized and regression-tested. Naming is configurable in templates, but the renderer deliberately blocks incompatible values.
- This feature renders roles, bootstrap/hierarchy, infrastructure, project source grants and role assignments. It does not fabricate missing live procedures, streams, semantic views, agents or Task DDL.
- Cortex model, agent, schedule and integration references in recovered SQL require explicit dependency review before text templating. Renderer does **not** automatically make those live objects configurable.
- Do not enable Task scheduling, email sends, Cortex calls, or arbitrary table grants by default.
- Never grant ADMIN, STEWARD and TASK_EXEC to every installer just because they're deploying; steward should be assigned to an approved reviewer.
- To ensure zero object loss, restore exact live definitions and satisfy `scripts/release_gate.py` first.
