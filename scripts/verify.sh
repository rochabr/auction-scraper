#!/usr/bin/env bash
set -euo pipefail
# Qualification is evidence-only staging aggregation; production smoke emits completion.json only after every gate passes.
# Implementation contract: Dispatch --suite smoke|load|recovery|qualification. Cloud controls belong to AKS smoke; staging rotation fixtures only, production read-only. See docs/execution.md and docs/operations.md.
printf '%s\n' 'Contract scaffold only: implement and verify this script before execution.' >&2
exit 2
