.phony: mo genstrings

mo:
	for f in *_tornado.po; do \
        mkdir -p ../captain/gettext/$${f%_tornado.po}/LC_MESSAGES && \
		msgfmt -o ../captain/gettext/$${f%_tornado.po}/LC_MESSAGES/tornado.mo $$f; done
	for f in *_static.po; do \
        mkdir -p ../captain/gettext/$${f%_static.po}/LC_MESSAGES && \
		msgfmt -o ../captain/gettext/$${f%_static.po}/LC_MESSAGES/static.mo $$f; done

msgmerge: captain.pot
	for f in *_tornado.po; do \
		msgmerge -U $$f captain.pot; done
	for f in *_static.po; do \
		msgmerge -U $$f static.pot; done

# Do not touch!
genstrings:
	egrep -h -o -R '(_|.translate)\("([^"]+)?"\)' ../captain \
		| sed -E -e 's/^(_|.translate)\(//g' -e 's/\)$$//g' -e 's/\\/\\\\/g' \
		| sort | uniq \
		| awk '{ print "msgid " $$0 "\n" "msgstr " $$0 "\n" }' \
		> captain.pot
