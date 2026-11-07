# Build the HTML report for every example
#   make report   - generate ./<example>/html for every example
#   make clean    - remove all generated reports
#   make help     - show this help

EXAMPLES := $(patsubst %/Makefile,%,$(wildcard */Makefile))

.PHONY: help report clean $(EXAMPLES)

help:
	@echo "Targets:"
	@echo "  make report  - generate the HTML report for every example"
	@echo "  make clean   - remove all generated reports"
	@echo "  make help    - show this help"
	@echo "Examples: $(EXAMPLES)"

report: $(EXAMPLES)

$(EXAMPLES):
	$(MAKE) -C $@ report

clean:
	@for e in $(EXAMPLES); do $(MAKE) -C $$e clean; done
