#!/usr/bin/env python3

import sys, os
import gettext
import subprocess
import gettext

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio


# i18n
gettext.install("pia-manager", "/usr/share/locale")

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

        gladefile = "/usr/share/pia-manager/main.ui"
        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)

        self.window = self.builder.get_object("main_window")
        self.username = self.builder.get_object("entry_username")
        self.password = self.builder.get_object("entry_password")
        self.gateway = self.builder.get_object("combobox_gateway")

        self.window.set_title("PIA")
        self.window.set_icon_name("pia-manager")

        # l10n        
        self.builder.get_object("label_username").set_text(_("PIA username"))
        self.builder.get_object("label_password").set_text(_("PIA password"))
        self.builder.get_object("label_gateway").set_text(_("Gateway"))        
        self.builder.get_object("checkbutton_show_password").set_label(_("Show password"))

        self.builder.get_object("checkbutton_show_password").connect("toggled", self.quit)
        self.builder.get_object("button_cancel").connect("clicked", self.on_quit)

        (username, password, gateway) = self.read_configuration()
        self.username.set_text(username)
        self.password.set_text(password)

        # Gateway combo
        model = Gtk.ListStore(str, str) #id, name
        selected_iter = None
        with open('/usr/share/pia-manager/gateways.list') as fp:
            for line in fp:
                line = line.strip()
                if not line.startswith("#"):
                    bits = line.split()
                    if len(bits) >= 2:
                        gateway_id = bits[0]
                        gateway_name = " ".join(bits[1:])
                        iter = model.append([gateway_id, gateway_name])
                        if gateway_id == gateway:
                            selected_iter = iter

        self.gateway.set_model(model)

        renderer = Gtk.CellRendererText()
        self.gateway.pack_start(renderer, True)
        self.gateway.add_attribute(renderer, "text", 1)

        if selected_iter is not None:
            self.gateway.set_active_iter(selected_iter)

        self.window.show()

        self.add_window(self.window)

    def on_show_password(self, checkbox):
        self.password.set_visibility(checkbox.get_active())

    def on_quit(self, button):
        self.quit()

    def read_configuration(self):
        username = ""
        password = ""
        gateway = None
        try:
            if os.path.exists('/etc/NetworkManager/system-connections/PIA'):
                with open('/etc/NetworkManager/system-connections/PIA') as fp:
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


if __name__ == "__main__":
    app = Manager()
    app.run(None)
