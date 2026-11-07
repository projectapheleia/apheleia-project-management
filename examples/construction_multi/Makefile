# Build the HTML report for this example into ./html
#   make report   - generate the report
#   make clean    - remove the generated report
#   make help     - show this help

HTML   ?= ./html
REPORT ?= apheleia_project_report

.PHONY: help report clean

help:
	@echo "Targets:"
	@echo "  make report  - generate the HTML report in $(HTML)"
	@echo "  make clean   - remove $(HTML)"
	@echo "  make help    - show this help"

report:
	$(REPORT) --input . --html $(HTML)

clean:
	rm -rf $(HTML)
