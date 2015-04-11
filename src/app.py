from gi.repository import Gdk, Gio, GLib, Gtk
import sys
import re
from redshift import RedshiftHelper
from threading import Thread, Event


class RedshiftApp(Gtk.Application):
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
            Gtk.STYLE_PROVIDER_PRIORITY_USER)

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

        hbox = Gtk.HBox(spacing=5)
        location_bt = Gtk.Button.new_from_icon_name('find-location-symbolic', Gtk.IconSize.BUTTON)
        """@type: Gtk.Button"""
        location_bt.connect('clicked', self.on_locationbt_clicked)
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

    def on_enabledbt_toggled(self, button: Gtk.ToggleButton):
        if button.get_active():
            self.helper.start()
        else:
            self.helper.stop()

    def on_locationbt_clicked(self, button):
        dialog = LocationDialog(self.window)
        dialog.latentry.set_text(str(self.helper.location[0]))
        dialog.lonentry.set_text(str(self.helper.location[1]))
        dialog.connect('response', self.on_locationdialog_response)
        dialog.run()

    def on_locationdialog_response(self, dialog, response):
        def get_entry_value(entry):
            if not re.match(r'^[-+]?\d*\.?\d+$', entry.get_text()):
                msg_dialog = Gtk.MessageDialog(self.window, type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK)
                if entry.get_text():
                    msg_dialog.set_markup("Invalid value: " + entry.get_text())
                else:
                    msg_dialog.set_markup("Fields cannot be empty!")
                msg_dialog.set_title("Error")
                msg_dialog.run()
                msg_dialog.destroy()
            else:
                return float(entry.get_text())

        if response == Gtk.ResponseType.OK:
            lat = get_entry_value(dialog.latentry)
            lon = None
            if lat:
                lon = get_entry_value(dialog.lonentry)
            if lon:
                self.helper.location = (lat, lon)
                dialog.destroy()
        else:
            dialog.destroy()

    def on_autotempradio_toggled(self, button: Gtk.RadioButton):
        active = button.get_active()
        self.builder.get_object('autotempgrid').set_sensitive(active)
        if active:
            dayadj = self.builder.get_object('daytempadj')
            nightadj = self.builder.get_object('nighttempadj')
            self.helper.temperature = (dayadj.get_value(), nightadj.get_value())

    def on_fixedtempradio_toggled(self, button):
        active = button.get_active()
        self.builder.get_object('fixedtempscale').set_sensitive(active)
        if active:
            adj = self.builder.get_object('fixedtempadj')
            self.helper.temperature = adj.get_value()

    def on_autobrightradio_toggled(self, button):
        active = button.get_active()
        self.builder.get_object('autobrightgrid').set_sensitive(active)
        if active:
            dayadj = self.builder.get_object('daybrightadj')
            nightadj = self.builder.get_object('nightbrightadj')
            self.helper.brightness = (dayadj.get_value() / 100, nightadj.get_value() / 100)

    def on_fixedbrightradio_toggled(self, button):
        active = button.get_active()
        self.builder.get_object('fixedbrightscale').set_sensitive(active)
        if active:
            adj = self.builder.get_object('fixedbrightadj')
            self.helper.brightness = adj.get_value() / 100

    def on_daytempadj_value_changed(self, adjustment):
        self.helper.temperature = (adjustment.get_value(), self.helper.temperature[1])

    def on_nighttempadj_value_changed(self, adjustment):
        self.helper.temperature = (self.helper.temperature[0], adjustment.get_value())

    def on_fixedtempadj_value_changed(self, adjustment):
        self.helper.temperature = adjustment.get_value()

    def on_daybrightadj_value_changed(self, adjustment):
        self.helper.brightness = (adjustment.get_value() / 100, self.helper.brightness[1])

    def on_nightbrightadj_value_changed(self, adjustment):
        self.helper.brightness = (self.helper.brightness[0], adjustment.get_value() / 100)

    def on_fixedbrightadj_value_changed(self, adjustment):
        self.helper.brightness = adjustment.get_value() / 100

    @staticmethod
    def on_tempscales_format_value(scale, value):
        return str(int(value)) + "K"

    @staticmethod
    def on_brightscales_format_value(scale, value):
        return str(int(value)) + "%"

    def on_about(self, *args):
        about = AboutDialog(self.helper, self.window)
        about.run()
        about.destroy()


class UpdateThread(Thread):
    def __init__(self, event, builder, redshifthelper, *args):
        Thread.__init__(self, *args)
        self.stopped = event
        self.builder = builder
        self.helper = redshifthelper
        self.labels = (
            self.builder.get_object('periodlabel'),
            self.builder.get_object('colortemplabel'),
            self.builder.get_object('brightnesslabel')
        )

    def run(self):
        self.update()
        while not self.stopped.wait(0.5):
            self.update()

    def update(self):
        info = self.helper.getinfo()
        Gdk.threads_enter()
        self.labels[0].set_markup(info[0])
        self.labels[1].set_markup('Color temperature: ' + info[1])
        self.labels[2].set_markup('Brightness: ' + str(int(float(info[2]) * 100)) + '%')
        Gdk.threads_leave()


class AboutDialog(Gtk.AboutDialog):
    def __init__(self, helper, parent=None):
        Gtk.AboutDialog.__init__(self, parent=parent)
        self.set_version('0.1\n' + helper.getname())
        self.set_logo_icon_name('redshift')
        self.set_website('https://github.com/ruci00/redshift-gui')
        self.set_website_label('GitHub')
        self.set_license_type(Gtk.License.GPL_2_0)
        self.set_authors(["Adam Rutkowski <a_rutkowski@outlook.com>"])
        self.set_destroy_with_parent(True)


class LocationDialog(Gtk.Dialog):
    def __init__(self, parent=None):
        Gtk.Dialog.__init__(self, title="Set location", parent=parent, use_header_bar=True)
        self.set_modal(True)
        grid = Gtk.Grid()
        grid.set_column_spacing(5)
        grid.set_row_spacing(5)
        grid.set_border_width(10)

        latlabel = Gtk.Label("Latitude:")
        grid.add(latlabel)
        self.latentry = Gtk.Entry()
        # self.latentry.connect('insert-text', self.on_lonlatentries_inserttext)
        grid.attach(self.latentry, 1, 0, 1, 1)
        lonlabel = Gtk.Label("Longitude:")
        grid.attach(lonlabel, 2, 0, 1, 1)
        self.lonentry = Gtk.Entry()
        # self.lonentry.connect('changed', self.on_lonentry_changed)
        grid.attach(self.lonentry, 3, 0, 1, 1)
        self.add_buttons("Cancel", Gtk.ResponseType.CANCEL,
                         "Save", Gtk.ResponseType.OK)
        self.get_content_area().add(grid)
        self.show_all()


class NoRedshiftDialog(Gtk.MessageDialog):
    def __init__(self):
        Gtk.MessageDialog.__init__(self, type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK)
        self.set_title("Redshift Settings")
        self.set_markup("Cannot find <i>redshift</i>! Program will be terminated.")

if __name__ == '__main__':
    redshift = RedshiftHelper()
    if not redshift.isavailable():
        NoRedshiftDialog().run()
        sys.exit()
    app = RedshiftApp(redshift)
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)

