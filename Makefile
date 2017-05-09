all: buildmo

buildmo:
	@echo "Building the mo files"
	# WARNING: the second sed below will only works correctly with the languages that don't contain "-"
	for file in `ls po/*.po`; do \
		lang=`echo $$file | sed 's@po/@@' | sed 's/.po//' | sed 's/pia-manager-//'`; \
		install -d usr/share/locale/$$lang/LC_MESSAGES/; \
		msgfmt -o usr/share/locale/$$lang/LC_MESSAGES/pia-manager.mo $$file; \
	done \

gksu:
	sed -i 's/gksu\|kdesu\|pkexec/gksu/g' "usr/bin/pia-manager"

pkexec:
	sed -i 's/gksu\|kdesu\|pkexec/pkexec/g' "usr/bin/pia-manager"

kdesu:
	sed -i 's/gksu\|kdesu\|pkexec/kdesu/g' "usr/bin/pia-manager"

install:
	cp -r usr/* /usr/
	glib-compile-schemas /usr/share/glib-2.0/schemas 2> /dev/null

uninstall:
	rm /usr/bin/pia-manager
	rm -r /usr/lib/pia-manager/
	rm -r /usr/share/pia-manager/
	rm /usr/share/applications/pia-manager.desktop

clean:
	rm -rf usr/share/locale
