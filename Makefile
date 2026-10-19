# Structural scaffold: operational targets deliberately fail until implemented.
.DEFAULT_GOAL := help
ENV ?= local
RUN_DIR ?=
PHASE ?= preflight
SUITE ?= smoke

.PHONY: help bootstrap doctor validate test build security publish local-up local-down infra-bootstrap infra-plan infra-apply configure-cluster deploy-dependencies migrate deploy verify rollback test-unit test-contracts test-integration test-regression test-evaluation
help:
	@printf '%s\n' 'Placeholder scaffold. Operational targets are not implemented.' 'See AGENTS.md and SCAFFOLD.md.'

bootstrap:
	@bash scripts/bootstrap.sh --env "$(ENV)" --run-dir "$(RUN_DIR)"

doctor:
	@bash scripts/doctor.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --phase "$(PHASE)"

validate:
	@bash scripts/validate.sh --env "$(ENV)" --run-dir "$(RUN_DIR)"

test:
	@bash scripts/test.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --suite all --test-path "$(TEST_PATH)"

build:
	@bash scripts/build.sh --env "$(ENV)" --run-dir "$(RUN_DIR)"

security:
	@bash scripts/security.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --release "$(RELEASE)"

publish:
	@bash scripts/publish.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --release "$(RELEASE)"

local-up:
	@bash scripts/local.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --action up --release "$(RELEASE)"

local-down:
	@bash scripts/local.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --action down

infra-bootstrap:
	@bash scripts/infra.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --action bootstrap

infra-plan:
	@bash scripts/infra.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --action plan

infra-apply:
	@bash scripts/infra.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --action apply --plan-manifest "$(PLAN_MANIFEST)"

configure-cluster:
	@bash scripts/cluster.sh --env "$(ENV)" --run-dir "$(RUN_DIR)"

deploy-dependencies:
	@bash scripts/dependencies.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --release "$(RELEASE)"

migrate:
	@bash scripts/migrate.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --release "$(RELEASE)"

deploy:
	@bash scripts/deploy.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --release "$(RELEASE)"

verify:
	@bash scripts/verify.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --suite "$(SUITE)" --release "$(RELEASE)"

rollback:
	@bash scripts/rollback.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --release-revision "$(RELEASE_REVISION)"

test-unit:
	@bash scripts/test.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --suite unit --test-path "$(TEST_PATH)"

test-contracts:
	@bash scripts/test.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --suite contracts --test-path "$(TEST_PATH)"

test-integration:
	@bash scripts/test.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --suite integration --test-path "$(TEST_PATH)"

test-regression:
	@bash scripts/test.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --suite regression --test-path "$(TEST_PATH)"

test-evaluation:
	@bash scripts/test.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --suite evaluation --test-path "$(TEST_PATH)"
