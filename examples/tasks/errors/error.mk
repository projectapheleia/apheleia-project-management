# Shared by every error case. The input is checked with --check, which is expected to FAIL, with an ERROR line
# containing $(EXPECT). The target fails if the check succeeds, fails with a different message, or writes anything.
#   make report   - check the input and check it fails as expected
#   make clean    - remove any output left by an earlier run

# Where a report would be written by default. --check must not write it
HTML   ?= ./html
REPORT ?= apheleia_project_report
# Report date, so the check is the same whatever day it is run. None for no report date
TODAY  ?= 2026-11-09

.PHONY: report clean

report:
	@$(RM) -r $(HTML)
	@out=$$($(REPORT) --check --input . --today $(TODAY) 2>&1); status=$$?; \
	echo "$$out"; \
	if [ $$status -eq 0 ]; then echo "FAIL: the check succeeded but was expected to fail"; exit 1; fi; \
	if ! echo "$$out" | grep -qF -- "ERROR :"; then echo "FAIL: exit status $$status but no ERROR line"; exit 1; fi; \
	if ! echo "$$out" | grep -qF -- "$(EXPECT)"; then echo "FAIL: expected an error containing: $(EXPECT)"; exit 1; fi; \
	if [ -e $(HTML) ]; then echo "FAIL: the check wrote $(HTML)"; exit 1; fi; \
	echo "OK: failed as expected (exit status $$status)"

clean:
	$(RM) -r $(HTML)
