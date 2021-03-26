
srcdir ?= .

all:

# Convenience rule to edit the UI file
GLADE ?= glade
GLADE_PREVIEWER ?= glade-previewer
GLADE_ENV := PYTHONPATH="$(srcdir)/glade:$$PYTHONPATH" \
	GLADE_CATALOG_SEARCH_PATH="$(srcdir)/glade:$$GLADE_CATALOG_SEARCH_PATH"
run-glade:
	$(GLADE_ENV) $(GLADE) $^
run-glade-previewer:
	$(GLADE_ENV) $(GLADE_PREVIEWER) --filename $^
run-glade: window.ui
run-glade-previewer: window.ui
