#!/usr/bin/env python3
"""Render safe, REVIEWABLE phase SQL from local YAML or JSON config.

Never executes SQL or connects to Snowflake. Standard-library JSON works without PyYAML.
Exactly recovered live DDL stays separate and is NOT templated by this program.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")
ORIGINAL_ROLES = {
    "admin": "VERITY_V1_0_ADMIN",
    "runtime_project_de": "VERITY_V1_0_EXEC_DE_PIPELINE",
    "steward": "VERITY_V1_0_STEWARD",
    "viewer": "VERITY_V1_0_VIEWER",
    "task_service": "VERITY_V1_0_TASK_EXEC",
}
ASSIGNMENTS = {
    "admin_users": "admin",
    "runtime_de_users": "runtime_project_de",
    "steward_users": "steward",
    "viewer_users": "viewer",
}
TEMPLATE_VAR = re.compile(r"{{\s*([a-z][a-z0-9_]*)\s*}}")


def render_sql_template(template_path, variables):
    """Deliberately limited Jinja-style renderer: allowlisted tokens, no code execution."""
    original = template_path.read_text(encoding="utf-8")
    def substitute(match):
        key = match.group(1)
        if key not in variables:
            raise ValueError(f"Missing or disallowed template variable {key!r} in {template_path}")
        return str(variables[key])
    output = TEMPLATE_VAR.sub(substitute, original)
    if "{{" in output or "}}" in output:
        raise ValueError(f"Unresolved or invalid placeholder in {template_path}")
    return output

RENDERED_GRANTS = [
    "01_project_runtime_hardened_base.sql",
    "03_steward_viewer.sql",
    "04_task_service.sql",
    "06_admin_creation_grants.sql",
]


def ident(value, field):
    if not isinstance(value, str) or not IDENT.fullmatch(value):
        raise ValueError(f"{field} must be an ordinary unquoted Snowflake identifier, got {value!r}")
    return value.upper()


def load_config(path):
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(raw)
    if path.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError as exc:
            raise ValueError("YAML requires PyYAML; use config/verity.deployment.example.json with Python stdlib instead") from exc
        return yaml.safe_load(raw)
    raise ValueError("Config must be .yaml/.yml or .json")


def valid_config(config):
    if not isinstance(config, dict):
        raise ValueError("Deployment config must be a mapping")
    db = ident(config.get("database"), "database")
    wh = ident(config.get("warehouse"), "warehouse")
    if db != "VERITY_V1_0" or wh != "VERITY_V1_0_WH":
        raise ValueError("V1 deployment is hardcoded to VERITY_V1_0 / VERITY_V1_0_WH in live procedure/Task DDL; renaming is blocked until refactored and retested")
    size = ident(config.get("warehouse_size", "XSMALL"), "warehouse_size")
    if size not in {"XSMALL", "SMALL", "MEDIUM", "LARGE", "XLARGE", "X2LARGE", "X3LARGE", "X4LARGE"}:
        raise ValueError("Unsupported warehouse_size")
    suspend = config.get("warehouse_auto_suspend_seconds", 60)
    if type(suspend) is not int or not 60 <= suspend <= 86400:
        raise ValueError("warehouse_auto_suspend_seconds must be integer between 60 and 86400")
    roles = config.get("roles", {})
    if set(ORIGINAL_ROLES) - set(roles):
        raise ValueError("Missing one or more required role names")
    roles = {key: ident(roles[key], f"roles.{key}") for key in ORIGINAL_ROLES}
    if len(set(roles.values())) != len(roles):
        raise ValueError("Role names must be distinct")
    assignments = config.get("role_assignments", {})
    if set(assignments) - set(ASSIGNMENTS):
        raise ValueError("Unknown role_assignments key")
    for key in ASSIGNMENTS:
        users = assignments.get(key, [])
        if not isinstance(users, list):
            raise ValueError(f"role_assignments.{key} must be a list")
        assignments[key] = sorted({ident(u, f"role_assignments.{key}") for u in users})
    if any(u in assignments.get('admin_users', []) for key in ('runtime_de_users','steward_users','viewer_users') for u in assignments.get(key, [])):
        raise ValueError("Admin identities must be reviewed separately; avoid mixing admin with end-user groups")
    srcs = config.get("project_sources", [])
    if not isinstance(srcs, list):
        raise ValueError("project_sources must be a list")
    approved = []
    for src in srcs:
        if not isinstance(src, dict) or type(src.get("approved")) is not bool:
            raise ValueError("Each project_sources entry needs name and Boolean approved")
        parts = str(src.get("name", "")).split(".")
        if len(parts) != 3:
            raise ValueError("Project source must be fully qualified DB.SCHEMA.TABLE")
        fqn = ".".join(ident(part, "project_sources.name") for part in parts)
        if src["approved"]:
            approved.append(tuple(fqn.split(".")))
    notify = config.get('notifications', {})
    if notify.get('enabled', False) not in (False, True):
        raise ValueError('notifications.enabled must be boolean')
    integration = ident(notify.get('integration', 'VERITY_V1_0_EMAIL_INT'), 'notifications.integration')
    task = config.get('scheduled_task', {})
    if task.get('enabled_on_install') is not False:
        raise ValueError('Task activation must be a separate explicit action; enabled_on_install must be false')
    bootstrap = config.get('bootstrap', {})
    if not isinstance(bootstrap, dict):
        raise ValueError('bootstrap must be a mapping')
    allowed_bootstrap = {'grant_admin_to_current_user', 'runtime_under_admin', 'admin_under_sysadmin'}
    if set(bootstrap) - allowed_bootstrap:
        raise ValueError('Unknown bootstrap configuration keys')
    for k in allowed_bootstrap:
        if type(bootstrap.get(k, k != 'grant_admin_to_current_user')) is not bool:
            raise ValueError(f'bootstrap.{k} must be boolean')
    return roles, assignments, sorted(set(approved)), size, suspend, integration, notify.get('enabled', False)


def replace_role_names(source, roles):
    # One pass avoids accidentally replacing a newly substituted role name.
    mapping = {original: roles[key] for key, original in ORIGINAL_ROLES.items()}
    pattern = re.compile(r"\b(?:" + "|".join(re.escape(v) for v in mapping) + r")\b")
    return pattern.sub(lambda hit: mapping[hit.group()], source)


def save(out, filename, content):
    path = out / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("-- AUTO-GENERATED from operator-provided config. REVIEW BEFORE RUNNING.\n" + content.rstrip() + "\n", encoding="utf-8")


def render(config_path, out):
    config = load_config(config_path)
    roles, assignments, sources, size, suspend, integration, notify_enabled = valid_config(config)
    out.mkdir(parents=True, exist_ok=True)
    bootstrap = config.get('bootstrap', {})
    admin_current_user = bootstrap.get('grant_admin_to_current_user', False)
    runtime_hierarchy = bootstrap.get('runtime_under_admin', True)
    sysadmin_hierarchy = bootstrap.get('admin_under_sysadmin', True)
    variables = {
        'admin_role': roles['admin'],
        'runtime_role': roles['runtime_project_de'],
        'steward_role': roles['steward'],
        'viewer_role': roles['viewer'],
        'task_service_role': roles['task_service'],
        'database': ident(config['database'], 'database'),
        'warehouse': ident(config['warehouse'], 'warehouse'),
        'warehouse_size': size,
        'warehouse_auto_suspend_seconds': suspend,
        'email_integration': integration,
        'admin_runtime_hierarchy_sql': (
            f"GRANT ROLE {roles['runtime_project_de']} TO ROLE {roles['admin']};"
            if runtime_hierarchy else '-- Not enabled: runtime_under_admin=false'),
        'sysadmin_hierarchy_sql': (
            f"GRANT ROLE {roles['admin']} TO ROLE SYSADMIN;"
            if sysadmin_hierarchy else '-- Not enabled: admin_under_sysadmin=false'),
        'self_grant_sql': (
            'SET VERITY_USER = (SELECT CURRENT_USER());\n'
            f"GRANT ROLE {roles['admin']} TO USER IDENTIFIER($VERITY_USER);"
            if admin_current_user else '-- Not enabled: bootstrap.grant_admin_to_current_user=false'
        ),
    }
    template_root = ROOT / 'sql/templates'
    for template_name, output_name in [
        ('01_roles/01_create_roles.sql.j2', '01_roles/01_create_roles.sql'),
        ('01_roles/02_role_hierarchy_and_bootstrap.sql.j2', '01_roles/02_role_hierarchy_and_bootstrap.sql'),
        ('02_infrastructure/01_database_warehouse_schemas.sql.j2', '02_infrastructure/01_database_warehouse_schemas.sql'),
    ]:
        save(out, output_name, render_sql_template(template_root/template_name, variables))
    for fname in RENDERED_GRANTS:
        source = (ROOT / 'sql/12_grants' / fname).read_text(encoding='utf-8')
        save(out, '12_grants/' + fname, replace_role_names(source, roles))
    # Project database/schema/source SELECT grants only when explicitly authorized.
    lines = ["-- Requires project table owner approval in source inventory."]
    if not sources:
        lines.append("-- NO APPROVED PROJECT SOURCES: no source SELECT grants generated.")
    for db, schema, table in sources:
        role = roles['runtime_project_de']
        lines.extend([
            f'GRANT USAGE ON DATABASE {db} TO ROLE {role};',
            f'GRANT USAGE ON SCHEMA {db}.{schema} TO ROLE {role};',
            f'GRANT SELECT ON TABLE {db}.{schema}.{table} TO ROLE {role};',
        ])
    save(out, '12_grants/02_project_approved_sources.sql', '\n'.join(lines))
    lines = ["-- USER MAPPING: apply only after explicit target-account admin approval.",
             "-- This file does not grant the internal TASK_EXEC role to any human."]
    if not any(assignments.values()):
        lines.append("-- NO USERS CONFIGURED. No role-to-user grants generated.")
    for key, role_key in ASSIGNMENTS.items():
        for username in assignments[key]:
            lines.append(f"GRANT ROLE {roles[role_key]} TO USER {username};")
    save(out, '12_grants/08_assign_roles_to_users.sql', '\n'.join(lines))
    # Email integration grant MUST be resolved after reviewing actual notifier owner/caller context.
    notification_review = f"""-- INTEGRATION {integration}: verify actual integration name and ALLOWED_RECIPIENTS.
-- Notification requested: {str(bool(notify_enabled)).upper()}.
-- NOT EXECUTABLE by default: inspect SP_DQ_NOTIFY_DRAFT_RULES DDL for EXECUTE AS.
-- Grant USAGE ON INTEGRATION to the effective execution role only after approval.
-- Example, if CALLER rights (verify before uncommenting):
-- GRANT USAGE ON INTEGRATION {integration} TO ROLE {roles['runtime_project_de']};
"""
    save(out, '12_grants/09_notification_REVIEW_FIRST.sql', notification_review)
    readme = [
        '# Generated deployment SQL — REVIEW, DO NOT BLINDLY EXECUTE',
        '',
        f'- Generated from: `{config_path.name}`',
        '- All names validated as unquoted Snowflake identifiers; user lists may be empty.',
        '- Fixed database and warehouse names are mandatory until source DDL is refactored.',
        '- Phase 01 uses literal {{ variable }} SQL templates; rendered SQL has no placeholders.',
        '- Bootstrap current-user ADMIN grant is OPT-IN via bootstrap.grant_admin_to_current_user.',
        '- Generated artifacts cover configurable roles, warehouse settings, approved sources, grants and user mapping.',
        '- Does NOT regenerate missing live tables/procedures/views/semantic views/agents/streams/tasks.',
        '- Never run user assignment SQL without named-account owner approval.',
        '- Task activation and email integration permission require explicit review.',
        '- `01_project_runtime_hardened_base.sql` excludes unsafe catalog INSERT.',
        '- Follow deploy/INSTALL_ORDER.md and scripts/release_gate.py.',
        '',
        'Apply `12_grants/04_task_service.sql` carefully: account-level EXECUTE TASK requires an account-level grant authority.',
    ]
    (out/'README.md').write_text('\n'.join(readme)+'\n', encoding='utf-8')
    # The configured manifest points to rendered role/infrastructure/grant SQL.
    # No missing live DDL paths are invented or marked present.
    manifest = json.loads((ROOT/'deploy/deployment_manifest.json').read_text(encoding='utf-8'))
    replacement = {
        '01': ['01_roles/01_create_roles.sql','01_roles/02_role_hierarchy_and_bootstrap.sql'],
        '02': ['02_infrastructure/01_database_warehouse_schemas.sql'],
        '12': [
            '12_grants/06_admin_creation_grants.sql',
            '12_grants/01_project_runtime_hardened_base.sql',
            '12_grants/02_project_approved_sources.sql',
            '12_grants/03_steward_viewer.sql',
            '12_grants/04_task_service.sql',
            '12_grants/09_notification_REVIEW_FIRST.sql',
            '12_grants/08_assign_roles_to_users.sql',
        ],
    }
    # Manifest paths are resolved relative to this generated manifest's directory.
    # References outside the generated directory are relative via ../.. when rendered at deploy/generated.
    import os
    for phase in manifest['phases']:
        if phase['phase'] in replacement:
            phase['files'] = [str(Path(p)) for p in replacement[phase['phase']]]
        else:
            phase['files'] = [os.path.relpath(ROOT / f, out) for f in phase['files']]
    manifest['note'] = ('Configured phase paths resolve from the directory containing this manifest. '
                        'REVIEW_FIRST and user-grant files must be approved separately; '
                        'live DDL is still missing until exported.')
    (out/'deployment_manifest.configured.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(f'Rendered config-aware SQL in {out} (roles={len(roles)}, users={sum(len(v) for v in assignments.values())}, approved_project_tables={len(sources)})')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--out', type=Path, default=ROOT / 'deploy/generated')
    args = parser.parse_args()
    try:
        render(args.config, args.out)
    except (ValueError, OSError, KeyError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
