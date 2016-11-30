#!/usr/bin/env python3

import sys, os
import gettext
import subprocess
import gettext
import uuid
import time

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio


# i18n
gettext.install("pia-manager", "/usr/share/locale")

CONFIGURATION = """[connection]
id=PIA
uuid=UUID
type=vpn
autoconnect=false
permissions=user:LINUX_USERNAME:;
secondaries=
timestamp=TIMESTAMP

[vpn]
username=PIA_USERNAME
comp-lzo=yes
remote=PIA_GATEWAY
connection-type=password
password-flags=0
ca=/usr/share/pia-manager/ca.crt
service-type=org.freedesktop.NetworkManager.openvpn

[vpn-secrets]
password=PIA_PASSWORD

[ipv4]
dns-search=
method=auto

[ipv6]
dns-search=
ip6-privacy=0
method=auto"""

CONFIG_FILE = '/etc/NetworkManager/system-connections/PIA'

class Manager(Gtk.Application):
    ''' Create the UI '''
    def __init__(self, linux_username):
        self.linux_username = linux_username
        Gtk.Application.__init__(self, application_id='com.pia.manager', flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self.on_activate)

    def on_activate(self, data=None):
        list = self.get_windows()
        if len(list) > 0:
            # Already running, focus the window
            self.get_active_window().present()
        else:
            self.create_window()

    def create_window(self):

        gladefile = "/usr/share/pia-manager/main.ui"
        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)

        self.window = self.builder.get_object("main_window")
        self.username = self.builder.get_object("entry_username")
        self.password = self.builder.get_object("entry_password")
        self.gateway = self.builder.get_object("combobox_gateway")
        self.button = self.builder.get_object("button_ok")

        self.window.set_title("PIA")
        self.window.set_icon_name("pia-manager")

        # l10n
        self.builder.get_object("label_username").set_text(_("PIA username"))
        self.builder.get_object("label_password").set_text(_("PIA password"))
        self.builder.get_object("label_gateway").set_text(_("Gateway"))
        self.builder.get_object("link_forgot_password").set_markup("<a href='#'>%s</a>" % _("Forgot password?"))

        (username, password, self.gateway_value) = self.read_configuration()
        self.username.set_text(username)
        self.password.set_text(password)

        # Gateway combo
        model = Gtk.ListStore(str, str) #id, name
        selected_iter = None
        # load list of gateways
        gateway_info = []
        try:
            with open('/usr/share/pia-manager/gateways.list.dynamic') as fp:
                gateway_info = fp.readlines()
        except IOError:
            with open('/usr/share/pia-manager/gateways.list') as fp:
                gateway_info = fp.readlines()

        for line in gateway_info:
            line = line.strip()
            if not line.startswith("#"):
                bits = line.split()
                if len(bits) >= 2:
                    gateway_id = bits[0]
                    gateway_name = " ".join(bits[1:])
                    iter = model.append([gateway_id, gateway_name])
                    if gateway_id == self.gateway_value:
                        selected_iter = iter

        self.gateway.set_model(model)

        renderer = Gtk.CellRendererText()
        self.gateway.pack_start(renderer, True)
        self.gateway.add_attribute(renderer, "text", 1)

        if selected_iter is not None:
            self.gateway.set_active_iter(selected_iter)

        self.window.show()

        self.add_window(self.window)

        # Signals
        self.builder.get_object("entry_password").connect("icon-press", self.on_entry_icon_pressed)
        self.builder.get_object("button_cancel").connect("clicked", self.on_quit)
        self.builder.get_object("link_forgot_password").connect("activate-link", self.on_forgot_password_clicked)
        self.username.connect("changed", self.check_entries)
        self.password.connect("changed", self.check_entries)
        self.gateway.connect("changed", self.on_combo_changed)
        self.button.connect("clicked", self.save_configuration)

    def on_entry_icon_pressed(self, entry, position, event):
        if position == Gtk.EntryIconPosition.SECONDARY:
            self.password.set_visibility(not self.password.get_visibility())

    def on_forgot_password_clicked(self, label, uri):
        subprocess.Popen(["su", "-c", "xdg-open https://www.privateinternetaccess.com/pages/reset-password.html", self.linux_username])
        return True

    def on_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter != None:
            model = combo.get_model()
            gateway_id, gateway_name = model[tree_iter][:2]
            self.gateway_value = gateway_id
            self.check_entries()

    def on_quit(self, button):
        self.quit()

    def read_configuration(self):
        username = ""
        password = ""
        gateway = None
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE) as fp:
                    for line in fp:
                        line = line.strip()
                        if not line.startswith("#"):
                            bits = line.split("=")
                            if len(bits) == 2:
                                if bits[0] == "username":
                                    username = bits[1]
                                elif bits[0] == "password":
                                    password = bits[1]
                                elif bits[0] == "remote":
                                    gateway = bits[1]
        except:
            pass # best
        return (username, password, gateway)

    def save_configuration(self, button):
        configuration = CONFIGURATION.replace("PIA_USERNAME", self.username.get_text())
        configuration = configuration.replace("PIA_PASSWORD", self.password.get_text())
        configuration = configuration.replace("PIA_GATEWAY", self.gateway_value)
        configuration = configuration.replace("LINUX_USERNAME", self.linux_username)
        configuration = configuration.replace("UUID", str(uuid.uuid4()))
        configuration = configuration.replace("TIMESTAMP", str(int(time.time())))
        with open(CONFIG_FILE, 'w') as fp:
            fp.writelines(configuration)
        os.system("chmod 600 %s" % CONFIG_FILE)
        os.system("service network-manager restart")
        self.button.set_sensitive(False)

    def check_entries(self, widget=None):
        if (self.username.get_text() != "" and self.password.get_text() != "" and self.gateway_value is not None):
            self.button.set_sensitive(True)
        else:
            self.button.set_sensitive(False)


if __name__ == "__main__":
    linux_username = sys.argv[1]
    app = Manager(linux_username)
    app.run(None)
