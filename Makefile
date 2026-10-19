# Structural scaffold: operational targets deliberately fail until implemented.
.DEFAULT_GOAL := help
ENV ?= local
RUN_DIR ?= artifacts/local/placeholder

.PHONY: help bootstrap doctor validate test build security publish local-up local-down infra-bootstrap infra-plan infra-apply configure-cluster deploy-dependencies migrate deploy verify rollback test-unit test-contracts test-integration test-regression test-evaluation
help:
	@printf '%s\n' 'Placeholder scaffold. Operational targets are not implemented.' 'See AGENTS.md and SCAFFOLD.md.'

bootstrap:
	@bash scripts/bootstrap.sh --env "$(ENV)" --run-dir "$(RUN_DIR)"

doctor:
	@bash scripts/doctor.sh --env "$(ENV)" --run-dir "$(RUN_DIR)"

validate:
	@bash scripts/validate.sh --env "$(ENV)" --run-dir "$(RUN_DIR)"

test:
	@bash scripts/test.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --suite all

build:
	@bash scripts/build.sh --env "$(ENV)" --run-dir "$(RUN_DIR)"

security:
	@bash scripts/security.sh --env "$(ENV)" --run-dir "$(RUN_DIR)"

publish:
	@bash scripts/publish.sh --env "$(ENV)" --run-dir "$(RUN_DIR)"

local-up:
	@bash scripts/local.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --action up

local-down:
	@bash scripts/local.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --action down

infra-bootstrap:
	@bash scripts/infra.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --action bootstrap

infra-plan:
	@bash scripts/infra.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --action plan

infra-apply:
	@bash scripts/infra.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --action apply

configure-cluster:
	@bash scripts/cluster.sh --env "$(ENV)" --run-dir "$(RUN_DIR)"

deploy-dependencies:
	@bash scripts/dependencies.sh --env "$(ENV)" --run-dir "$(RUN_DIR)"

migrate:
	@bash scripts/migrate.sh --env "$(ENV)" --run-dir "$(RUN_DIR)"

deploy:
	@bash scripts/deploy.sh --env "$(ENV)" --run-dir "$(RUN_DIR)"

verify:
	@bash scripts/verify.sh --env "$(ENV)" --run-dir "$(RUN_DIR)"

rollback:
	@bash scripts/rollback.sh --env "$(ENV)" --run-dir "$(RUN_DIR)"

test-unit:
	@bash scripts/test.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --suite unit

test-contracts:
	@bash scripts/test.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --suite contracts

test-integration:
	@bash scripts/test.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --suite integration

test-regression:
	@bash scripts/test.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --suite regression

test-evaluation:
	@bash scripts/test.sh --env "$(ENV)" --run-dir "$(RUN_DIR)" --suite evaluation
