# The simple example with no report date. Nothing is marked as today, forecasts start from each task's latest
# status update, and stale tasks, the current milestone and availability are checked against the latest status
# update in the input. Build the HTML report into ./html
#   make report   - generate the report
#   make clean    - remove the generated report
#   make help     - show this help

HTML   ?= ./html
INPUT  ?= ../../simple
REPORT ?= apheleia_project_report
# Report date. None for a report with no date
TODAY  ?= None

.PHONY: help report clean

help:
	@echo "Targets:"
	@echo "  make report  - generate the HTML report of $(INPUT), with no report date, in $(HTML)"
	@echo "  make clean   - remove $(HTML)"
	@echo "  make help    - show this help"

report:
	@$(REPORT) --input $(INPUT) --html $(HTML) --today $(TODAY); status=$$?; \
	if [ $$status -ne 0 ]; then echo "FAIL: $(REPORT) exited with status $$status, expected 0"; exit 1; fi; \
	echo "OK: report generated in $(HTML) (exit status 0)"

clean:
	rm -rf $(HTML)
