#!/usr/bin/python3

import sys, os
import gettext
import subprocess
import gettext
import uuid
import time
import json
import urllib.request
import setproctitle

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

setproctitle.setproctitle('pia-manager')

# i18n
gettext.install("pia-manager", "/usr/share/locale")

CONFIGURATION = """[connection]
id=PIA
uuid=UUID
type=vpn
autoconnect=false
permissions=
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

TMP_CONFIG_FILE = os.path.expanduser("~/.config/pia-manager/PIA")
os.system("mkdir -p ~/.config/pia-manager")

CONFIG_FILE = '/etc/NetworkManager/system-connections/PIA'
SKIP_DNS_KEY = 'skip-dns-resolution'

class Manager(Gtk.Application):
    ''' Create the UI '''
    def __init__(self):
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

        self.settings = Gio.Settings(schema="com.pia.manager")
        self.skip_dns = self.settings.get_boolean(SKIP_DNS_KEY)

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

        self.builder.get_object("link_forgot_password").set_markup("<a href='#'>%s</a>" % self.builder.get_object("link_forgot_password").get_text())

        (username, password, self.gateway_value) = self.read_configuration()
        self.username.set_text(username)
        self.password.set_text(password)

        renderer = Gtk.CellRendererText()
        self.gateway.pack_start(renderer, True)
        self.gateway.add_attribute(renderer, "text", 1)

        self.load_combo()

        self.window.show()

        self.add_window(self.window)

        self.infobar = self.builder.get_object("infobar")
        self.infobar.hide()

        # Configuration
        self.use_ip_addresses_checkbox = self.builder.get_object("menuitem_skip_dns")
        self.use_ip_addresses_checkbox.set_active(self.skip_dns)

        # Signals
        self.use_ip_addresses_checkbox.connect("toggled", self.on_menuitem_use_ip_addresses_toggled)
        self.builder.get_object("menuitem_quit").connect("activate", self.on_quit)
        self.builder.get_object("menuitem_help_contents").connect("activate", self.on_menuitem_help_contents_activated)
        self.builder.get_object("menuitem_help_about").connect("activate", self.on_menuitem_help_about_activated)
        self.builder.get_object("entry_password").connect("icon-press", self.on_entry_icon_pressed)
        self.builder.get_object("button_cancel").connect("clicked", self.on_quit)
        self.builder.get_object("link_forgot_password").connect("activate-link", self.on_forgot_password_clicked)
        self.builder.get_object("button_refresh").connect("clicked", self.on_button_refresh_clicked)
        self.username.connect("changed", self.check_entries)
        self.password.connect("changed", self.check_entries)
        self.gateway.connect("changed", self.on_combo_changed)
        self.button.connect("clicked", self.save_configuration)

    def on_button_refresh_clicked(self, button):
        self.infobar.hide()
        self.download_latest_gateways()
        self.load_combo()

    def on_menuitem_use_ip_addresses_toggled(self, menuitem):
        self.skip_dns = menuitem.get_active()
        self.settings.set_boolean(SKIP_DNS_KEY, self.skip_dns)
        self.download_latest_gateways()
        self.load_combo()

    def load_combo(self):
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

        if selected_iter is not None:
            self.gateway.set_active_iter(selected_iter)

    def download_latest_gateways(self):
        """Updates the list of PIA gateways. If 'skip-dns-resolution' is true, store IP addresses rather than hostnames."""
        # TODO: also update the CRL from this call, can be handled in similar way most likely.
        # grab new gateway json
        response = urllib.request.urlopen('https://privateinternetaccess.com/vpninfo/servers?version=24')
        data = response.read()
        text = data.decode('utf-8')

        # split json from CRL blob
        server_info_text, crl = text.split('\n\n')
        server_info = json.loads(server_info_text)

        # assemble file that the manager uses
        gateway_info = {}
        for key, info in server_info.items():
            if key == 'info':
                continue

            host = info['dns']
            if self.skip_dns:
                host = info['openvpn_udp']['best'].split(':')[0]

            gateway_info[key] = '{host} {name}'.format(host=host, name=info['name'])

        # arrange by the region list we prefer
        gateway_list = []
        for key in server_info['info']['auto_regions']:
            gateway_list.append(gateway_info[key])

        gateways = '\n'.join(gateway_list)

        # write out file
        with open('/usr/share/pia-manager/gateways.list.dynamic', 'w') as fp:
            fp.write(gateways)

    def on_entry_icon_pressed(self, entry, position, event):
        if position == Gtk.EntryIconPosition.SECONDARY:
            self.password.set_visibility(not self.password.get_visibility())

    def on_forgot_password_clicked(self, label, uri):
        subprocess.Popen(["xdg-open", "https://www.privateinternetaccess.com/pages/reset-password.html"])
        return True # needed to suppress the link callback in Gtk.Entry

    def on_menuitem_help_contents_activated(self, menuitem):
        subprocess.Popen(["xdg-open", "https://helpdesk.privateinternetaccess.com"])

    def on_menuitem_help_about_activated(self, menuitem):
        dlg = Gtk.AboutDialog()
        dlg.set_program_name(_("PIA Manager"))
        dlg.set_icon_name("pia-manager")
        dlg.set_transient_for(self.window)
        dlg.set_logo_icon_name("pia-manager")
        dlg.set_website("http://www.github.com/linuxmint/pia-manager")
        try:
            for path in ["/usr/share/common-licenses/GPL-3"]:
                if os.path.exists(path):
                    h = open(path, 'r')
                    s = h.readlines()
                    gpl = ""
                    for line in s:
                        gpl += line
                    h.close()
                    dlg.set_license(gpl)
        except Exception as e:
            print (e)
            print(sys.exc_info()[0])

        if os.path.exists("/usr/lib/linuxmint/common/version.py"):
            version = subprocess.getoutput("/usr/lib/linuxmint/common/version.py pia-manager")
            dlg.set_version(version)

        def close(w, res):
            if res == Gtk.ResponseType.CANCEL or res == Gtk.ResponseType.DELETE_EVENT:
                w.hide()
        dlg.connect("response", close)
        dlg.show()

    def on_combo_changed(self, combo):
        self.infobar.hide()
        tree_iter = combo.get_active_iter()
        if tree_iter != None:
            model = combo.get_model()
            gateway_id, gateway_name = model[tree_iter][:2]
            self.gateway_value = gateway_id
            self.check_entries()

    def on_quit(self, widget):
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
            # If we can't read the config file, we use dconf
            username = self.settings.get_string("username")
            password = self.settings.get_string("password")
            gateway = self.settings.get_string("gateway")
        return (username, password, gateway)

    def save_configuration(self, button):
        username = self.username.get_text()
        password = self.password.get_text()
        gateway = self.gateway_value
        self.settings.set_string("username", username)
        self.settings.set_string("password", password)
        self.settings.set_string("gateway", gateway)
        configuration = CONFIGURATION.replace("PIA_USERNAME", username)
        configuration = configuration.replace("PIA_PASSWORD", password)
        configuration = configuration.replace("PIA_GATEWAY", gateway)
        configuration = configuration.replace("UUID", str(uuid.uuid4()))
        configuration = configuration.replace("TIMESTAMP", str(int(time.time())))
        with open(TMP_CONFIG_FILE, 'w') as fp:
            fp.writelines(configuration)
        os.system("pkexec /usr/lib/pia-manager/apply-pia-configuration %s" % TMP_CONFIG_FILE)
        self.button.set_sensitive(False)
        if os.path.exists(TMP_CONFIG_FILE):
            os.unlink(TMP_CONFIG_FILE)
        else:
            self.infobar.show()

    def check_entries(self, widget=None):
        self.infobar.hide()
        if (self.username.get_text() != "" and self.password.get_text() != "" and self.gateway_value is not None):
            self.button.set_sensitive(True)
        else:
            self.button.set_sensitive(False)

if __name__ == "__main__":
    app = Manager()
    app.run(None)
