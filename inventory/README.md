# Source-account inventory reconciliation (mandatory)

Copy `source_inventory.example.csv` to `source_inventory.csv` and REPLACE the example with **all actual** source objects from the `SHOW` catalog output: schemas, tables, sequences, views, semantic views, procedures (all overloads), UDFs, streams, tasks, stages, file formats, policies, tags, agents, and integrations (note account objects separately). Every source inventory record must map to a real install file or an explicit justified external dependency. `scripts/release_gate.py` rejects missing inventory and any untracked extra object. Export role grants and counts to `grants_source.csv` (private if names are sensitive), record table row counts separately.

Raw DDL and data must be backed up outside Snowflake before account expiry, even if not safe to commit to a Git repo.
