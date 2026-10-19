# Configuration schema ownership

Before enabling validation, replace each fail-closed schema with a strict JSON Schema matching its source YAML. Reject unknown keys, invalid ranges, unsupported environments and inconsistent references. Runtime/production readiness additionally rejects unresolved required identity, endpoint, contact, price, source-version and signature references.

Environment files use config/environment.schema.json; policy files use config/schemas/<basename>.schema.json. deploy/platform-sources.yaml uses platform-sources.schema.json. Validate rendered chart values separately against each chart's values.schema.json.

Null discovery fields keep the scaffold non-runnable. Do not weaken production schema requirements to accept them. Offline tests use an explicit isolated test configuration, never a production bypass.
