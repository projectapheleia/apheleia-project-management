# Shared by every error case. The report is expected to FAIL, with an ERROR line containing $(EXPECT).
# The target fails if the report succeeds, fails with a different message, or generates a report.
#   make report   - run the report and check it fails as expected
#   make clean    - remove any generated report

HTML   ?= ./html
REPORT ?= apheleia_project_report
# Report date, so the report is the same whatever day it is run. None for a report with no date
TODAY  ?= 2026-11-09

.PHONY: report clean

report:
	@$(RM) -r $(HTML)
	@out=$$($(REPORT) --input . --html $(HTML) --today $(TODAY) 2>&1); status=$$?; \
	echo "$$out"; \
	if [ $$status -eq 0 ]; then echo "FAIL: the report succeeded but was expected to fail"; exit 1; fi; \
	if ! echo "$$out" | grep -qF -- "ERROR :"; then echo "FAIL: exit status $$status but no ERROR line"; exit 1; fi; \
	if ! echo "$$out" | grep -qF -- "$(EXPECT)"; then echo "FAIL: expected an error containing: $(EXPECT)"; exit 1; fi; \
	if [ -e $(HTML)/index.html ]; then echo "FAIL: a report was generated"; exit 1; fi; \
	echo "OK: failed as expected (exit status $$status)"

clean:
	$(RM) -r $(HTML)
