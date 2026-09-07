# Entry points for the local maintenance pipeline (see docs/ai-automation-pipeline.md).
#
#   make doctor                     check this machine can run the pipeline
#   make scan                       stage 1: read-only gap scan of every configured repo
#   make scan REPO=owner/name       scan just one repository
#   make triage                     stage 2: show the issues that would be filed
#   make triage APPLY=1             actually file them
#   make status                     what is pending per repository
#   make test                       offline test suite (no tokens, no network)
#
# Pick the executor with AGENT_CMD: codex (default), claude, or stub.
#   make scan AGENT_CMD=claude

AGENT_CMD ?= codex
REPO      ?=
LIMIT     ?=
CONFIG    ?=
APPLY     ?= 0
ENRICH    ?= 0

export AGENT_CMD

BIN := pipeline/bin
TRUTHY := 1 yes true on

repo_arg   = $(if $(REPO),--repo $(REPO))
config_arg = $(if $(CONFIG),--config $(CONFIG))
limit_arg  = $(if $(LIMIT),--limit $(LIMIT))
apply_arg  = $(if $(filter $(APPLY),$(TRUTHY)),--apply)
enrich_arg = $(if $(filter $(ENRICH),$(TRUTHY)),--enrich)

.PHONY: help doctor scan triage status test

help:
	@sed -n '1,12p' Makefile | sed 's/^# \{0,1\}//'

doctor:
	@$(BIN)/doctor.sh

scan:
	@$(BIN)/scan.sh $(repo_arg) $(config_arg)

triage:
	@$(BIN)/triage.sh $(repo_arg) $(config_arg) $(limit_arg) $(apply_arg) $(enrich_arg)

status:
	@python3 $(BIN)/lib/state.py --state-dir $${PIPELINE_STATE_DIR:-pipeline/state} status

test:
	@pipeline/tests/run-tests.sh
