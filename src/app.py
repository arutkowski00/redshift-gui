from gi.repository import Gdk, Gio, GLib, Gtk
import sys
import os
from redshift import RedshiftHelper
from threading import Thread, Event


class RedshiftApp(Gtk.Application):
    is_enabled = None
    update_stopflag = Event()

    def __init__(self, redshifthelper):
        Gtk.Application.__init__(self)
        GLib.set_prgname("Redshift Settings")
        self.helper = redshifthelper
        """@type: RedshiftHelper"""
        self.statusicon = Gtk.StatusIcon()
        self.builder = Gtk.Builder()
        self.builder.add_from_file('ui.glade')
        self.builder.connect_signals(self)
        self.window = self.builder.get_object('window')
        """@type : Gtk.Window """

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
        enabled_bt = Gtk.ToggleButton()
        enabled_bt.set_image(powerimage)
        enabled_bt.set_tooltip_text('Enable/disable Redshift')
        enabled_bt.connect('toggled', self.on_enabledbt_toggled)
        # TODO: add toggling event handler
        headerbar.pack_start(enabled_bt)

        self.is_enabled = enabled_bt.get_active
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

        UpdateThread(self.update_stopflag, self.builder, self.helper, ).start()
        self.helper.start()
        self.window.show_all()

    def do_startup(self):
        Gtk.Application.do_startup(self)

        aboutaction = Gio.SimpleAction.new('about', None)
        aboutaction.connect('activate', self.on_about)
        self.add_action(aboutaction)

    def on_window_delete_event(self, *args):
        self.helper.stop()
        self.update_stopflag.set()
        Gtk.main_quit()

    def on_enabledbt_toggled(self, *args):
        pass

    def on_autotempradio_toggled(self, *args):
        pass

    def on_fixedbrightradio_toggled(self, *args):
        pass

    def on_autobrightradio_toggled(self, *args):
        pass

    def on_fixedtempradio_toggled(self, *args):
        pass

    def on_about(self, *args):
        about = AboutDialog(self.helper)
        about.set_transient_for(self.window)
        about.run()
        about.destroy()


class UpdateThread(Thread):
    def __init__(self, event, builder, redshifthelper, *args):
        Thread.__init__(self, *args)
        self.stopped = event
        self.builder = builder
        self.helper = redshifthelper

    def run(self):
        self.update()
        while not self.stopped.wait(0.5):
            self.update()

    def update(self):
        info = self.helper.getinfo()
        labels = (
            self.builder.get_object('periodlabel'),
            self.builder.get_object('colortemplabel'),
            self.builder.get_object('brightnesslabel')
        )
        Gdk.threads_enter()
        labels[0].set_markup(info[0])
        labels[1].set_markup('Color temperature: ' + info[1])
        labels[2].set_markup('Brightness: ' + str(int(float(info[2]) * 100)) + '%')
        Gdk.threads_leave()


class AboutDialog(Gtk.AboutDialog):
    def __init__(self, helper):
        Gtk.AboutDialog.__init__(self)
        self.set_version('0.1\n' + helper.getname())
        self.set_logo_icon_name('redshift')
        self.set_website('https://github.com/ruci00/redshift-gui')
        self.set_website_label('GitHub')
        self.set_license_type(Gtk.License.GPL_2_0)
        self.set_authors(["Adam Rutkowski <a_rutkowski@outlook.com>"])
        self.set_destroy_with_parent(True)

if __name__ == '__main__':
    redshift = RedshiftHelper()
    if not redshift.isavailable():
        msg = Gtk.MessageDialog(type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK)
        msg.set_title("Redshift Settings")
        msg.set_markup("Cannot find <i>redshift</i>! Program will be terminated.")
        msg.run()
        sys.exit()
    app = RedshiftApp(redshift)
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)

