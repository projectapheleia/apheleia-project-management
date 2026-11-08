# Build every resource example
#   make report   - build the availability report, then check every error case fails as expected
#   make clean    - remove all generated reports
#   make help     - show this help

SUBDIRS := availability errors

.PHONY: help report clean $(SUBDIRS)

help:
	@echo "Targets:"
	@echo "  make report  - build the availability report, then check every error case fails as expected"
	@echo "  make clean   - remove all generated reports"
	@echo "  make help    - show this help"
	@echo "Entries: $(SUBDIRS)"

report: $(SUBDIRS)

$(SUBDIRS):
	$(MAKE) -C $@ report

clean:
	@for e in $(SUBDIRS); do $(MAKE) -C $$e clean; done
