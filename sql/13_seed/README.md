# Data restore and seed order
1. Create all object DDL first. Do not copy historical IDs to live tables by default.
2. Load sanitized source sample tables under their owning project roles.
3. Register approved sources via audited onboarding (once secured), not bulk modify catalog.
4. Stage/approve expected standard rule fixtures under a reviewed steward process.
5. Historical `RESULTS.*` can be archived separately, but old stream offsets, queue backlog and Task status cannot be blindly replayed in target account.
6. `DQ_SOURCE` IDs, rule IDs and `RUN_ID`s may differ after reinstall; tests must query by FQN/attributes, never assume IDs 501/701.
