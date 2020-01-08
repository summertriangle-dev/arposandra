.phony mo:
	for f in *.po; do \
        mkdir -p ../captain/gettext/$${f%.po}/LC_MESSAGES && \
		msgfmt -o ../captain/gettext/$${f%.po}/LC_MESSAGES/tornado.mo $$f; done
