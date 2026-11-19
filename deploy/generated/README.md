# Generated deployment SQL — REVIEW, DO NOT BLINDLY EXECUTE

- Generated from: `verity.deployment.example.json`
- All names validated as unquoted Snowflake identifiers; user lists may be empty.
- Fixed database and warehouse names are mandatory until source DDL is refactored.
- Phase 01 uses literal {{ variable }} SQL templates; rendered SQL has no placeholders.
- Bootstrap current-user ADMIN grant is OPT-IN via bootstrap.grant_admin_to_current_user.
- Generated artifacts cover configurable roles, warehouse settings, approved sources, grants and user mapping.
- Does NOT regenerate missing live tables/procedures/views/semantic views/agents/streams/tasks.
- Never run user assignment SQL without named-account owner approval.
- Task activation and email integration permission require explicit review.
- `01_project_runtime_hardened_base.sql` excludes unsafe catalog INSERT.
- Follow deploy/INSTALL_ORDER.md and scripts/release_gate.py.

Apply `12_grants/04_task_service.sql` carefully: account-level EXECUTE TASK requires an account-level grant authority.
