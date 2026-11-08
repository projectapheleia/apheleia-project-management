# Run every example and report whether it passed
#   make report   - run every example, printing "<example> : PASSED" or "<example> : FAILED" for each
#                   as it finishes, then the number passed and failed. Fails if any example failed.
#                   Run "make -C <example> report" to see the output of a failed example.
#                   Examples are independent, so "make -j report" runs them in parallel
#   make clean    - remove all generated reports
#   make help     - show this help

# An example is any directory with a Makefile that has no directory below it with a Makefile
TESTS := $(shell for m in $$(find . -mindepth 2 -name Makefile | sort); do \
                   d=$$(dirname $$m); \
                   [ -z "$$(find $$d -mindepth 2 -name Makefile)" ] && echo $$d | sed 's|^\./||'; \
                 done)

# Directory holding the result of each example, so the summary can count them however many jobs are run
RESULTS := .report-results

.PHONY: help report clean init summary $(TESTS:%=test/%) $(TESTS:%=clean/%)

help:
	@echo "Targets:"
	@echo "  make report  - run every example and report PASSED or FAILED for each (-j to run in parallel)"
	@echo "  make clean   - remove all generated reports"
	@echo "  make help    - show this help"
	@echo "Examples: $(TESTS)"

report: summary

init:
	@$(RM) -r $(RESULTS)
	@mkdir -p $(RESULTS)
	@echo "Running $(words $(TESTS)) tests:"

# Each example prints and records its result, and never fails, so every example runs and the summary is printed
$(TESTS:%=test/%): test/%: | init
	@if $(MAKE) --no-print-directory -C $* report >/dev/null 2>&1; then r=PASSED; else r=FAILED; fi; \
	echo "$* : $$r" > $(RESULTS)/$(subst /,__,$*); \
	echo "$* : $$r"

# Runs once every example has finished
summary: $(TESTS:%=test/%)
	@pass=$$(cat $(RESULTS)/* | grep -c ' : PASSED$$'); \
	fail=$$(cat $(RESULTS)/* | grep -c ' : FAILED$$'); \
	$(RM) -r $(RESULTS); \
	echo "$$pass passed, $$fail failed"; \
	[ $$fail -eq 0 ]

clean: $(TESTS:%=clean/%)
	@$(RM) -r $(RESULTS)
	@echo "cleaned $(words $(TESTS)) examples"

$(TESTS:%=clean/%): clean/%:
	@$(MAKE) --no-print-directory -C $* clean >/dev/null 2>&1 || { echo "$* : CLEAN FAILED"; exit 1; }
