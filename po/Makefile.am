LANGUAGES=hu

EXTRA_DIST=hu.po

all: $(foreach lang,$(LANGUAGES),$(lang).mo)

.PHONY: jsprog.pot
jsprog.pot:
	xgettext --from-code="utf-8" -o $@ $(top_srcdir)/src/client/jsprog/*.py $(top_srcdir)/src/client/jsprog/gui/*.py

mergepo: jsprog.pot
	for lang in $(LANGUAGES); do msgmerge -U $(srcdir)/$${lang}.po jsprog.pot; done

.po.mo:
	msgfmt -o $@ $^

install: $(foreach lang,$(LANGUAGES),$(lang).mo)
	for lang in $(LANGUAGES); do dir="$(DESTDIR)$(localedir)/$${lang}/LC_MESSAGES"; mkdir -p "$${dir}"; $(INSTALL) $${lang}.mo "$${dir}/jsprog.mo" ; done
