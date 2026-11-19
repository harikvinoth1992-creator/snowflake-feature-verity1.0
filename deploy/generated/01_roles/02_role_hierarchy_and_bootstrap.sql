-- AUTO-GENERATED from operator-provided config. REVIEW BEFORE RUNNING.
-- TEMPLATE ONLY: owner must approve role hierarchy and self-grant.
USE ROLE SECURITYADMIN;
-- ADMIN inherits only RUNTIME; STEWARD and TASK_SERVICE remain separate.
GRANT ROLE VERITY_V1_0_EXEC_DE_PIPELINE TO ROLE VERITY_V1_0_ADMIN;
GRANT ROLE VERITY_V1_0_ADMIN TO ROLE SYSADMIN;

-- Current Snowflake session user, not a hardcoded username.
-- Not enabled: bootstrap.grant_admin_to_current_user=false
