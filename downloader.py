#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, time
import gtk, gobject
import constants
import utils
import subprocess
import xmlrpclib
from threading import Thread

class Aria2c:
    def __init__(self):
        pid = os.getpid()
        command = ['aria2c', '--enable-rpc', '--continue', '--stop-with-process=%s' % pid, '--file-allocation=none']
        subprocess.Popen(command, shell=True)
        self.aria2 = xmlrpclib.ServerProxy('http://localhost:6800/rpc').aria2
    
    def add_download(self, args):
        if args[0] == 'addUri':
            return self.aria2.addUri(args[1].get('uris'), args[1].get('options'))

    def format_list_store_line_from_status(self, gid):
        s = self.aria2.tellStatus(gid)
        
        status = utils.convert_status_to_stock_id(s.get("status"))
        f = s.get("files")[0]
        name = os.path.basename(f.get("path")) if f.get("path") else "未知"
        length = float(f.get("length"))
        completedLength = float(f.get("completedLength"))
        progress = completedLength/length*100.0 if length!=0 else 0
        precent = "%.1f" % progress
        precent += "%"
        down_status = "%s/%s" % ("已完成" if length!=0 and completedLength==length else utils.bytes_to_human(completedLength),
            utils.bytes_to_human(length))
        down_speed = utils.bytes_to_human(s.get("downloadSpeed"))
        down_speed += "/s"
        return [status, name, progress, precent, down_status, down_speed]

aria2 = Aria2c()

class MainWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)

        self.set_size_request(600, 350)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_title(constants.__app_name__+" "+ constants.__version__)
        self.set_icon_from_file("app_icon.png")
        
        vbox = gtk.VBox(False, 5)
        
        hbox = gtk.HBox(True, 3)
        ctrl_button_align = gtk.Alignment(0.0, 0.5, 0.5, 0.0)
        hbox.pack_start(ctrl_button_align)
        search_entry_align = gtk.Alignment(1.0, 0.5, 0.8, 0.0)
        hbox.pack_end(search_entry_align)

        new_button = gtk.Button("新建")
        preference_button = gtk.Button("设置")
        clear_button = gtk.Button("清除")
        button_hbox = gtk.HBox(True, 0)
        button_hbox.pack_start(new_button, True, True, 5)
        button_hbox.pack_start(preference_button, True, True, 5)
        button_hbox.pack_start(clear_button, True, True, 5)
        ctrl_button_align.add(button_hbox)

        search_entry = gtk.Entry()
        search_entry.set_icon_from_stock(1, gtk.STOCK_FIND)
        search_entry.set_text("搜索已下载的文件...")
        search_entry.connect('focus-in-event', self.cursor_in_search_entry)
        search_entry.connect('focus-out-event', self.cursor_out_search_entry)
        search_hbox = gtk.HBox(False, 5)
        search_hbox.pack_start(search_entry, True, True, 5)
        search_entry_align.add(search_hbox)

        vbox.pack_start(hbox, False, False, 5)
        
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        vbox.pack_start(scrolled_window)

        self.task_list_store = gtk.ListStore(
            gobject.TYPE_STRING, # 状态
            gobject.TYPE_STRING, # 文件名称
            gobject.TYPE_FLOAT,  # 进度值
            gobject.TYPE_STRING, # 进度百分比
            gobject.TYPE_STRING, # 已下载状态
            gobject.TYPE_STRING) # 下载速度
        self.task_list = TaskListView(self.task_list_store)
        scrolled_window.add(self.task_list)

        self.status_bar = gtk.Statusbar()
        vbox.pack_start(self.status_bar, False, False, 0)

        self.add(vbox)
        self.connect('destroy', gtk.main_quit)
        self.show_all()

        self.task_data = TaskData()
        
        new_button.connect("clicked", self.new_button_action)

    def new_button_action(self, widget):
        d = NewDownloadDialog(self)
        response = d.run()
        if response == gtk.RESPONSE_OK:
            uri = d.address_entry.get_text().strip()
            folder = d.folder_entry.get_text().strip()
            args = ["addUri",
                {'uris': [uri],
                'options': {"dir": folder},
                }]
            u = UpdateStatus(args, self.task_data, self.task_list_store)
            u.start()
        d.destroy()
        
    def addUri_test(self, widget):
        args = ["addUri", 
            {'uris': ['http://127.0.0.1/f/bubu_1.mp4'],
            'options': {"dir":utils.get_default_save_dir()},
            }]
        u = UpdateStatus(args, self.task_data, self.task_list_store)
        u.start()

    def loop(self):
        gtk.main()

    def cursor_in_search_entry(self, widget, event):
        if widget.get_text() == "搜索已下载的文件...":
            widget.set_text('')

    def cursor_out_search_entry(self, widget, event):
        if widget.get_text() == '':
            widget.set_text('搜索已下载的文件...')

class NewDownloadDialog(gtk.Dialog):
    def __init__(self, parent):
        super(NewDownloadDialog, self).__init__("新建下载", parent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)

        self.add_button("下载", gtk.RESPONSE_OK)
        self.add_button("取消", gtk.RESPONSE_CANCEL)

        self.set_size_request(400, 120)

        vbox = self.get_content_area()

        table = gtk.Table(3, 3)

        address_label = gtk.Label("下载地址:")
        address_label.set_width_chars(10)
        self.address_entry = gtk.Entry()
        table.attach(address_label, 0, 1, 0, 1, xoptions=gtk.SHRINK)
        table.attach(self.address_entry, 1, 3, 0, 1)

        folder_label = gtk.Label("下载到:")
        folder_label.set_width_chars(10)
        self.folder_entry = gtk.Entry()
        self.folder_entry.set_text(utils.get_default_save_dir())
        self.choose_folder_button = gtk.Button("浏览")
        self.choose_folder_button.connect("clicked", self.display_folder_chooser_dialog)
        table.attach(folder_label, 0, 1, 1, 2, xoptions=gtk.SHRINK)
        table.attach(self.folder_entry, 1, 2, 1, 2)
        table.attach(self.choose_folder_button, 2, 3, 1, 2, yoptions=gtk.SHRINK)
        
        vbox.pack_start(table)
        self.show_all()

    def display_folder_chooser_dialog (self, widget):
        dialog = gtk.FileChooserDialog(
                "选择目录", 
                self, 
                gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, 
                (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            )
        dialog.set_current_folder(utils.get_default_save_dir())
        dialog.set_position(gtk.WIN_POS_CENTER)
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self.folder_entry.set_text(dialog.get_filename())
        dialog.destroy()

class UpdateStatus(Thread):
    def __init__(self, args, data, list_store):
        super(UpdateStatus, self).__init__()
        self.args = args
        self.data = data
        self.list_store = list_store
        self.complete = False

    def run(self):
        gid = aria2.add_download(self.args)
        while not self.complete:
            try:
                new_status = aria2.format_list_store_line_from_status(gid)
            except Exception, e:
                print "\nError:%s" % e
                break
            
            _iter = self.data.get_from_gid(gid)
            if _iter:
                for i in range(len(new_status)):
                    self.list_store.set_value(_iter, i, new_status[i])
            else:
                _iter = self.list_store.append(new_status)
                self.data.append(gid, _iter)
            if new_status[0] == 'gtk-apply':
                self.complete = True

class TaskListView(gtk.TreeView):
    def __init__(self, model):
        gtk.TreeView.__init__(self, model)
        
        column = gtk.TreeViewColumn("状态")
        column.set_expand(False)
        column.set_resizable(False)
        self.append_column(column)
        renderer = gtk.CellRendererPixbuf()
        column.pack_start(renderer, False)
        column.add_attribute(renderer, 'stock-id', 0)

        column = gtk.TreeViewColumn("文件")
        column.set_expand(False)
        column.set_resizable(True)
        column.set_min_width(50)
        column.set_max_width(150)
        self.append_column(column)
        renderer = gtk.CellRendererText()
        column.pack_start(renderer, False)
        column.add_attribute(renderer, 'text', 1)

        column = gtk.TreeViewColumn("下载进度")
        column.set_expand(True)
        column.set_resizable(True)
        self.append_column(column)
        renderer = gtk.CellRendererProgress()
        column.pack_start(renderer, True)
        column.add_attribute(renderer, 'value', 2)
        column.add_attribute(renderer, 'text', 3)

        column = gtk.TreeViewColumn("已下载")
        column.set_expand(False)
        column.set_resizable(True)
        self.append_column(column)
        renderer = gtk.CellRendererText()
        column.pack_start(renderer, False)
        column.add_attribute(renderer, 'text', 4)

        column = gtk.TreeViewColumn("速度")
        column.set_expand(False)
        column.set_resizable(True)
        self.append_column(column)
        renderer = gtk.CellRendererText()
        column.pack_start(renderer, False)
        column.add_attribute(renderer, 'text', 5)

class TaskData(object):
    def __init__(self):
        self._gid_list = []
        self._iter_list = []

    def append(self, _gid, _iter):
        if utils.is_in_list(self._gid_list, _gid) == False and utils.is_in_list(self._iter_list, _iter) == False:
            self._gid_list.append(_gid)
            self._iter_list.append(_iter)
            return True
        else:
            print "values pairs already be saved: %s-%s" % (_gid, _iter)
            return False
    
    def get_from_gid(self, _gid):
        if utils.is_in_list(self._gid_list, _gid):
            index = self._gid_list.index(_gid)
            return self._iter_list[index]
        else:
            return None

    def get_from_iter(self, _iter):
        if utils.is_in_list(self._iter_list, _iter):
            index = self._iter_list.index(_iter)
            return self._gid_list[index]
        else:
            return None

    def remove_from_gid(self, _gid):
        if utils.is_in_list(self._gid_list, _gid):
            index = self._gid_list.index(_gid)
            self._iter_list.remove(self._iter_list[index])
            self._gid_list.remove(_gid)
            return True
        else:
            return False

    def remove_from_iter(self, _iter):
        if utils.is_in_list(self._iter_list, _iter):
            index = self._iter_list.index(_iter)
            self._gid_list.remove(self._gid_list[index])
            self._iter_list.remove(_iter)
            return True
        else:
            return False

if __name__ == '__main__':
    gtk.gdk.threads_init()
    win = MainWindow()
    win.loop()
    
