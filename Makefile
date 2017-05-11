all: buildmo

buildmo:
	@echo "Building the mo files"
	# WARNING: the second sed below will only works correctly with the languages that don't contain "-"
	for file in `ls po/*.po`; do \
		lang=`echo $$file | sed 's@po/@@' | sed 's/.po//' | sed 's/pia-manager-//'`; \
		install -d usr/share/locale/$$lang/LC_MESSAGES/; \
		msgfmt -o usr/share/locale/$$lang/LC_MESSAGES/pia-manager.mo $$file; \
	done \

sudo:
	sed -i 's/sudo\|gksu\|kdesu\|pkexec/sudo/g' "usr/bin/pia-manager"

gksu:
	sed -i 's/sudo\|gksu\|kdesu\|pkexec/gksu/g' "usr/bin/pia-manager"

pkexec:
	sed -i 's/sudo\|gksu\|kdesu\|pkexec/pkexec/g' "usr/bin/pia-manager"

kdesu:
	sed -i 's/sudo\|gksu\|kdesu\|pkexec/kdesu/g' "usr/bin/pia-manager"

install:
	cp -r usr/* /usr/
	glib-compile-schemas /usr/share/glib-2.0/schemas 2> /dev/null
	xdg-icon-resource forceupdate

uninstall:
	rm -f /usr/bin/pia-manager
	rm -rf /usr/lib/pia-manager/
	rm -rf /usr/share/pia-manager/
	rm -f /usr/share/applications/pia-manager.desktop
	rm -f `find /usr/share/icons/hicolor -name pia-manager.png`
	rm -f /usr/share/icons/hicolor/scalable/actions/pia-manager-*.svg

clean:
	rm -rf usr/share/locale
