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

        self.window.set_title("Private Internet Access")
        self.window.set_icon_name("pia-manager")

        self.window.show()

        self.add_window(self.window)   

if __name__ == "__main__":
    app = Manager()
    app.run(None)
