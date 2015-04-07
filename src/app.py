from gi.repository import Gdk, Gio, GLib, Gtk
import sys
import os


class RedshiftApp(Gtk.Application):
    enabled_bt = None

    def __init__(self):
        Gtk.Application.__init__(self)
        GLib.set_prgname("Redshift settings")
        self.statusicon = Gtk.StatusIcon()
        self.builder = Gtk.Builder()
        self.builder.add_from_file('ui.glade')
        self.builder.connect_signals(self)
        self.window = self.builder.get_object('window')

        styleprovider = Gtk.CssProvider()
        styleprovider.load_from_path('ui.css')
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),
            styleprovider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def build_headerbar(self):
        headerbar = Gtk.HeaderBar()
        headerbar.set_title(self.window.get_title())
        headerbar.set_show_close_button(True)
        powerimage = Gtk.Image()
        powerimage.set_from_icon_name('system-shutdown-symbolic', Gtk.IconSize.BUTTON)
        self.enabled_bt = Gtk.ToggleButton()
        self.enabled_bt.set_image(powerimage)
        self.enabled_bt.set_tooltip_text('Enable/disable Redshift')
        # TODO: add toggling event handler
        headerbar.pack_start(self.enabled_bt)

        hbox = Gtk.HBox(spacing=5)
        location_bt = Gtk.Button.new_from_icon_name('find-location-symbolic', Gtk.IconSize.BUTTON)
        menu_bt = Gtk.MenuButton()
        menuimage = Gtk.Image()
        menuimage.set_from_icon_name('open-menu-symbolic', Gtk.IconSize.BUTTON)
        menu_bt.set_image(menuimage)

        popovermenu = Gio.Menu()
        popovermenu.append("About", "app.about")

        popover = Gtk.Popover().new_from_model(menu_bt, popovermenu)
        menu_bt.set_popover(popover)

        hbox.add(location_bt)
        hbox.add(menu_bt)
        headerbar.pack_end(hbox)

        self.window.set_titlebar(headerbar)

    def do_activate(self):
        self.window.set_application(self)
        self.build_headerbar()

        self.window.show_all()

    def do_startup(self):
        Gtk.Application.do_startup(self)

        aboutaction = Gio.SimpleAction.new('about', None)
        aboutaction.connect('activate', self.on_about)
        self.add_action(aboutaction)

    def on_window_delete_event(self, *args):
        Gtk.main_quit()

    def on_autotempradio_toggled(self, *args):
        pass

    def on_fixedbrightradio_toggled(self, *args):
        pass

    def on_autobrightradio_toggled(self, *args):
        pass

    def on_fixedtempradio_toggled(self, *args):
        pass

    def on_about(self, *args):
        about = AboutDialog()
        about.set_transient_for(self.window)
        about.run()
        about.destroy()


class AboutDialog(Gtk.AboutDialog):
    def __init__(self):
        Gtk.AboutDialog.__init__(self)
        self.set_version('0.1')
        self.set_logo_icon_name('redshift')
        self.set_website('https://github.com/ruci00/redshift-gui')
        self.set_website_label('GitHub')
        self.set_license_type(Gtk.License.GPL_2_0)
        self.set_authors(["Adam Rutkowski <a_rutkowski@outlook.com>"])
        self.set_destroy_with_parent(True)

if __name__ == '__main__':
    app = RedshiftApp()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)

