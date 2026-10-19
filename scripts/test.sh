#!/usr/bin/env bash
set -euo pipefail
# Implementation contract: Accept --suite unit|contracts|integration|regression|evaluation|all and optional --test-path. Isolated Compose only; no live Azure/providers. Required empty/skipped suites fail.
printf '%s\n' 'Contract scaffold only: implement and verify this script before execution.' >&2
exit 2
