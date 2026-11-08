# Check that every invalid task definition is rejected by the report
#   make report   - run every case; each must fail with the expected error
#   make clean    - remove all generated reports
#   make help     - show this help

CASES := $(patsubst %/Makefile,%,$(wildcard */Makefile))

.PHONY: help report clean $(CASES)

help:
	@echo "Targets:"
	@echo "  make report  - run every case; each must fail with the expected error"
	@echo "  make clean   - remove all generated reports"
	@echo "  make help    - show this help"
	@echo "Entries: $(CASES)"

report: $(CASES)

$(CASES):
	$(MAKE) -C $@ report

clean:
	@for e in $(CASES); do $(MAKE) -C $$e clean; done
