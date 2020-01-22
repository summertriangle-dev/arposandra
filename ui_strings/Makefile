.phony: mo genstrings

mo:
	for f in *.po; do \
        mkdir -p ../captain/gettext/$${f%.po}/LC_MESSAGES && \
		msgfmt -o ../captain/gettext/$${f%.po}/LC_MESSAGES/tornado.mo $$f; done

msgmerge: captain.pot
	for f in *.po; do \
		msgmerge -U $$f captain.pot; done

# Do not touch!
genstrings:
	egrep -h -o -R '(_|.translate)\("([^"]+)?"\)' ../captain \
		| sed -E -e 's/^(_|.translate)\(//g' -e 's/\)$$//g' -e 's/\\/\\\\/g' \
		| sort | uniq \
		| awk '{ print "msgid " $$0 "\n" "msgstr " $$0 "\n" }' \
		> captain.pot
