-- ACCOUNTADMIN / CREATE INTEGRATION-privileged role.
-- DO NOT RUN until actual integration name and verified recipients established.
-- Example only; uncomment and customize via reviewed admin change:
-- CREATE NOTIFICATION INTEGRATION IF NOT EXISTS VERITY_V1_0_EMAIL_INT
--   TYPE=EMAIL ENABLED=TRUE ALLOWED_RECIPIENTS=('verified-user@example.com');
-- Verified recipients must belong to users with verified email in target Snowflake account.
SHOW NOTIFICATION INTEGRATIONS;
-- DESCRIBE INTEGRATION VERITY_V1_0_EMAIL_INT;
-- Grant USAGE only to effective caller/owner that calls SYSTEM$SEND_EMAIL.
