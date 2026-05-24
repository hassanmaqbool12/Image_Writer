import gi
gi.require_version("Gtk", "3.0")

import os
import re
import sys
import json
import threading
import subprocess
from gi.repository import Gtk, GLib, Gdk

PATH = os.path.dirname(__file__)
ARGV = None

class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.carbon.image-writer")
        GLib.set_application_name("USB Image Writer")
        self.usb_model = "USB Flash"
        self.size = 0
        self.to_format = False
        self.name = None
        self.iso_path = None
        self.usb = None
        self.usb_dic = {}
        self.usb_id = None
        self.has_usb = True


    def do_activate(self):
        self.window = Gtk.ApplicationWindow(application=self)
        self.window.set_resizable(False)

        #   CSS style providing is here.

        styler = Gtk.CssProvider()
        styler.load_from_path(PATH+"/style.css")
        display = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(display, styler, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        #   Widgets are here

        self.body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        self.success = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        self.box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.box3 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        self.box4 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.successLogo = Gtk.Image.new_from_icon_name("dialog-info", Gtk.IconSize.BUTTON)
        self.successLogo.set_pixel_size(60)
        self.successText = Gtk.Label(label="Image written successfully")
        self.successButton = Gtk.Button(label="Write another USB")

        self.isoLabel = Gtk.Label(label="ISO image:")

        self.isoBox = Gtk.Button()

        self.semiBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.isoName = Gtk.Label(label="(None)")
        self.chooser = Gtk.Image.new_from_icon_name("folder-open-symbolic", Gtk.IconSize.BUTTON)

        self.usbLabel = Gtk.Label(label="USB stick: ")

        self.usBox = Gtk.ComboBoxText()
        self.usBox.set_active(0)

        self.bar = Gtk.ProgressBar()
        self.log = Gtk.Label()

        self.write = Gtk.Button(label="Write")
        self.cancel = Gtk.Button(label="Cancel")

        #   CSS naming goes here.

        self.body.set_name("body")
        self.box3.set_name("box3")
        self.bar.set_name("bar")
        self.successButton.set_name("vip-bt")
        self.successLogo.set_name("vip-logo")
        self.write.set_name("buttons")
        self.cancel.set_name("buttons")

        #   Properties management is here.

        self.box.set_hexpand(True)
        self.box1.set_hexpand(True)
        self.box2.set_hexpand(True)
        self.box3.set_hexpand(True)

        self.box1.set_size_request(200, -1)
        self.box2.set_size_request(200, -1)
        self.box3.set_size_request(200, -1)

        self.box1.set_halign(Gtk.Align.CENTER)
        self.box2.set_halign(Gtk.Align.CENTER)
        self.box3.set_halign(Gtk.Align.END)
        self.box4.set_halign(Gtk.Align.END)

        self.isoBox.set_size_request(290, -1)
        self.usBox.set_size_request(290, 35)
        self.bar.set_size_request(290, -1)

        self.isoLabel.set_halign(Gtk.Align.END)
        self.isoBox.set_halign(Gtk.Align.END)

        self.isoName.set_halign(Gtk.Align.START)
        self.chooser.set_halign(Gtk.Align.END)

        self.bar.set_fraction(0)

        self.bar.set_halign(Gtk.Align.END)

        self.cancel.set_halign(Gtk.Align.END)
        self.write.set_halign(Gtk.Align.END)

        # Connections are here.

        self.window.connect('destroy', self.kill)
        self.isoBox.connect("clicked", self.open_dialog)
        self.successButton.connect("clicked", self.switch_screens)
        self.write.connect("clicked", self.start)
        self.cancel.connect("clicked", self.kill)

        #   ADD and PACK_START are here.

        self.box1.pack_start(self.isoLabel, False, True, 0)
        self.box1.pack_start(self.isoBox, False, True, 0)

        self.semiBox.pack_start(self.isoName, True, True, 0)
        self.semiBox.pack_start(self.chooser, True, True, 0)

        self.isoBox.add(self.semiBox)

        self.box2.pack_start(self.usbLabel, False, True, 0)
        self.box2.pack_start(self.usBox, False, True, 0)

        self.box3.pack_start(self.bar, True, False, 0)
        self.box3.pack_start(self.log, True, False, 0)

        self.box4.pack_start(self.cancel, True, False, 0)
        self.box4.pack_start(self.write, True, False, 0)

        self.box.pack_start(self.box1, True, True, 0)
        self.box.pack_start(self.box2, True, True, 0)
        self.box.pack_start(self.box3, True, True, 0)
        self.box.pack_start(self.box4, True, True, 0)

        self.success.pack_start(self.successLogo, True, False, 0)
        self.success.pack_start(self.successText, True, False, 0)
        self.success.pack_start(self.successButton, True, False, 0)

        self.body.pack_start(self.box, True, True, 0)
        self.body.pack_start(self.success, True, True, 0)

        self.window.add(self.body)
        self.window.show_all()
        GLib.idle_add(self.scanUSB)
        GLib.idle_add(self.refresh)
        GLib.idle_add(self.add_options)
        self.success.set_visible(False)
        
        return
    
    def refresh(self):
        if ARGV is not None:
            self.update_iso(ARGV)

        self.to_format = False
        if self.has_usb:
            self.usBox.set_sensitive(True)
        else:
            self.usBox.set_sensitive(False)

        if self.iso_path is not None and self.usb is not None:
            self.write.set_sensitive(True)
        else:
            self.write.set_sensitive(False)

        self.bar.set_visible(False)

        return
    
    def switch_screens(self, widget):
        if self.box.is_visible():
            self.success.set_visible(True)
            self.box.set_visible(False)

        else:
            self.box.set_visible(True)
            self.success.set_visible(False)
        
        GLib.idle_add(self.scanUSB)
        GLib.idle_add(self.add_options)
        GLib.idle_add(self.refresh)
        return
    
    def add_options(self):
        for usb in self.usb_dic.values():
            text = f"{usb['model']} {usb['vendor']} ({usb['path']}) - {usb['size']}"
            self.usBox.append(usb['vendor'] ,text)
        
        self.usBox.connect("changed", self.on_changed)
        return
    
    def on_changed(self, c):
        text = c.get_active_id()
        self.usb = self.usb_dic[text]['path']
        self.usb_model = self.usb_dic[text]['model']
        self.usb_id = self.usb_dic[text]['name']
        self.refresh()
        return
    
    def start(self, widget):
        threading.Thread(target=self.make_image, daemon=True).start()
        return
    
    def show_format_dialog(self):
        self.dialog = Gtk.MessageDialog(
            parent=self.window,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            text=f"Are you sure you want to format '{self.usb_model}'?"
        )
        self.dialog.format_secondary_text(
            f"If you formatted, all existing data in {self.usb} will be erased."
        )

        self.dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.dialog.add_button("Format", Gtk.ResponseType.OK)
        self.dialog.set_default_response(Gtk.ResponseType.OK)

        self.dialog.set_title("USB is not empty")

        def on_response(widget, response):
            widget.destroy()
            if response == Gtk.ResponseType.OK:
                self.to_format = True
                GLib.idle_add(self.start, None)
            return

        self.dialog.connect("response", on_response)
        self.dialog.show_all()
        return
    
    def show_error_dialog(self, text, sectext):
        self.dialog = Gtk.MessageDialog(
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            text=text
        )
        self.dialog.format_secondary_text(sectext)
    
    def update_iso(self, path):
        if os.path.exists(path):
            self.iso_path = path
            self.name = os.path.basename(self.iso_path)
            self.size = os.path.getsize(self.iso_path)
            self.isoName.set_label(self.name)
        return
    
    def log_label(self, text):
        self.log.set_text(text)
        GLib.timeout_add(3000, self.log.set_text, '')
        return
    
    def on_file_selected(self, dialog, response):
        if response == Gtk.ResponseType.OK:
            self.update_iso(dialog.get_filename())
        dialog.destroy()
        self.refresh()
        return
    
    def open_dialog(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select Image File",
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons('Select', Gtk.ResponseType.OK)
        dialog.add_buttons('Close', Gtk.ResponseType.CANCEL)
        filter = Gtk.FileFilter()
        filter.set_name("ISO Files")
        filter.add_pattern("*.iso")
        filter.add_pattern("*.img")

        dialog.add_filter(filter)
        dialog.connect("response", self.on_file_selected)
        dialog.show()
        return
    
    def get_childs(self, name):
        try:
            cmd = ['lsblk', '-J']
            data = {}
            out = subprocess.check_output(cmd, text=True)
            data_in_json = json.loads(out)
            for each in data_in_json['blockdevices']:
                if each['name'] == name:
                    data['parent'] = each['name']
                    if each['mountpoints'][0] is None:
                        data['mounted'] = False
                    else:
                        data['mounted'] = True
                    
                    if each.get('children'):
                        childs = []
                        for child in each.get('children'):
                            each_child = []
                            each_child.append(child['name'])

                            if child.get('mountpoints')[0] is None:
                                each_child.append(False)
                            else:
                                each_child.append(True)
                                
                            each_child.append(child['mountpoints'])

                            childs.append(each_child.copy())
                            each_child.clear()

                        data['childs'] = childs
                    break
            return data
        
        except:
            return False
        
    def umount(self, path):
        try:
            if not os.path.exists(path):
                return 
            
            p = subprocess.run(['udisksctl', 'unmount', '-b', path], text=True, capture_output=True)
            if p.returncode == 0:
                return True
            
            return False
        except:
            return False
    
    def init_umount(self, data):
        parent = data.get('parent')
        childs = data.get('childs')
        if parent and data.get('mounted') is True:
            if not self.umount('/dev/'+parent):
                return False
        
        if len(childs) == 0:
            return True
        
        for child in childs:
            if child[1]:
                if self.check_iso(self.iso_path, child[2][0]):
                    GLib.idle_add(self.log_label, "Cannot use the provided iso, Because of it's path")
                    return False
                
                if not self.umount('/dev/'+child[0]):
                    GLib.idle_add(self.log_label, f"Unable to unmount {child[0]}")
                    return False
        
        return True
    
    def init(self, name):
        GLib.idle_add(self.log_label, 'Preparing to unmount')
        data = self.get_childs(name)
        if not data:
            GLib.idle_add(self.log_label, "Cannot find the USB")
            return False
        
        if not self.init_umount(data):
            return False
        
        GLib.idle_add(self.log_label, 'Preparing to write image')

        return True
    
    def get_mount_dev(self, path):
        path = os.path.realpath(path)

        while path != "/":
            if os.path.ismount(path):
                return os.stat(path).st_dev
            path = os.path.dirname(path)

        return None
    
    def check_iso(self, iso_path, usb_path):
        result = self.get_mount_dev(iso_path) == self.get_mount_dev(usb_path)
        return result

    def make_image(self):

        if self.iso_path and not os.path.exists(self.iso_path):
            GLib.idle_add(self.log_label, "Invalid image file Path")
            return True

        if not self.init(self.usb_id):
            return True
        
        self.bytes_written = 0
      
        cmd = ["pkexec", "dd", f"if={self.iso_path}", f"of={self.usb}", "bs=4M", "status=progress", "oflag=sync"]

        if self.iso_path and self.usb and os.path.exists(self.iso_path) and os.path.exists(self.usb):

            if os.path.getsize(self.usb) <= 0 and not self.to_format:
                GLib.idle_add(self.show_format_dialog)
                return

            try:
                p = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True)

                # UI Unit is here.

                GLib.idle_add(self.write.set_sensitive, False)
                GLib.idle_add(self.isoBox.set_sensitive, False)
                GLib.idle_add(self.usBox.set_sensitive, False)
                GLib.idle_add(self.bar.set_visible, True)\
                
                if p.stderr:
                    for line in p.stderr:   # IGNORE This error. I don't know but some how this do not crashes

                        m = re.search(r"(\d+)\s+bytes", line)

                        if m:
                            self.bytes_written = int(m.group(1))
                            percent = (self.bytes_written / self.size)
                            GLib.idle_add(self.bar.set_fraction, percent)
                            
                    p.wait()

            except:
                pass

        if (self.bytes_written / self.size) > 0:
            GLib.idle_add(self.refresh)
            GLib.idle_add(self.switch_screens, None)
        
        GLib.idle_add(self.write.set_sensitive, True)
        GLib.idle_add(self.isoBox.set_sensitive, True)
        GLib.idle_add(self.usBox.set_sensitive, True)
        GLib.idle_add(self.bar.set_visible, False)

        return
    
    def scanUSB(self):
        out = subprocess.check_output([
            "lsblk", "-J", "-o", "NAME,VENDOR,PATH,SIZE,MODEL,TRAN,RM,TYPE,MOUNTPOINT"
        ], text=True)

        data = json.loads(out)
        self.usb_dic.clear()

        for d in data["blockdevices"]:
            if d.get("type") == "disk" and d.get("tran") == "usb" and d["vendor"] not in self.usb_dic:
                self.usb_dic[d['vendor']] = ({
                    "name" : d['name'], 
                    "vendor" : d['vendor'],
                    "path" : d["path"],
                    "model" : d.get("model"),
                    "size" : d.get("size")
                    })
        return
    
    def kill(self, widget):
        os._exit(1)

if __name__=='__main__':
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        ARGV = sys.argv[1]
    app = App()
    app.run()