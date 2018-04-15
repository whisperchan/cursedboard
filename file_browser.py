import os
import magic
import sys
import hashlib

import npyscreen
import curses

from config import *
from utils import *
from controller import ActionController
from post_form import MaxTitleText

class DeleteFileForm(npyscreen.ActionPopup):
    OK_BUTTON_TEXT = "Delete!"
    CANCEL_BUTTON_TEXT = "Cancel"
    CANCEL_BUTTON_BR_OFFSET = (2, 16)
    DEFAULT_LINES = 10
    DEFAULT_COLUMNS = 80

    def create(self):
        self.value = None
        self.wgLabel = self.add(npyscreen.FixedText)
        self.wgLabel.editable = False
        self.wgPassword = self.add(MaxTitleText, name="Password:", max_length=MAX_CHARS_TITLE)

    def edit(self):
        if not self.before_editing_passed:
            self.parentApp.switchFormPrevious()
        else: 
            super(DeleteFileForm, self).edit()

    def beforeEditing(self):
        self.before_editing_passed = False
        global_filename = self.parentApp.myFile

        if not is_in_sftp(global_filename):
            return

        if not os.path.isfile(global_filename):
            return

        local_filename = global_filename[len(SFTP_ROOT_DIR):].split("/")

        if len(local_filename) != 3:
            return

        
        m = re.match("(^[0-9]+)_",local_filename[2])
        if not m:
            return
        
        pid = 0
        try:
            pid = int(m.group(1), 10)
        except:
            return
        

        bid = self.parentApp.myDatabase.name_to_bid(local_filename[0])
        if not bid:
            return

        tid = 0
        bid = int(bid[0])
        try:
            tid = int(local_filename[1], 10)
        except:
            return

        self.hash = self.parentApp.myDatabase.get_hash(bid, tid, pid)
        if not self.hash:
            return

        self.wgLabel.value = "Delete File: /{}?".format(global_filename[len(SFTP_ROOT_DIR):])
        self.before_editing_passed = True

    def on_ok(self):
        if not self.hash['hash'] or not self.hash['salt']: 
            self.parentApp.switchFormPrevious()

        hashphrase = hashlib.pbkdf2_hmac('sha256', self.wgPassword.value.encode("utf-8"), self.hash['salt'], 100000)

        if hashphrase != self.hash['hash']:
            self.parentApp.switchFormPrevious()

        os.remove(self.parentApp.myFile)
        self.parentApp.switchFormPrevious()

    def on_cancel(self):
        self.wgPassword.value = ""
        self.parentApp.switchFormPrevious()

class TextViewer(npyscreen.FormMuttActiveTraditional):
    ACTION_CONTROLLER = ActionController
    MAIN_WIDGET_CLASS = npyscreen.Pager
    def __init__(self, *args, **keywords):
        super(TextViewer, self).__init__(*args, **keywords)

    def beforeEditing(self,):
        self.add_handlers({
            curses.KEY_BACKSPACE: self.parentApp.switchFormPrevious,
        })

        self.value = self.parentApp.myFile
        if not os.path.isfile(self.value):
            self.parentApp.switchFormPrevious()

        with open(self.value,'r') as content:
            self.wMain.values = content.readlines()

class FileGrid(npyscreen.SimpleGrid):
    default_column_number = 1

    def __init__(self, *args, **keywords):
        super(FileGrid, self).__init__(*args, **keywords)
        self.select_whole_line = True
    
    def set_up_handlers(self):
        super(FileGrid, self).set_up_handlers()
        self.handlers.update ({
            curses.ascii.NL:    self.h_select_file,
            curses.ascii.CR:    self.h_select_file,
            curses.ascii.SP:    self.h_select_file,
            curses.KEY_DC: self.delete_file,
        })
    
    def change_dir(self, select_file):
        try:
            os.listdir(select_file)
        except OSError:
            npyscreen.notify_wait(title="Error", message="Cannot enter directory.")
            return False
        self.parent.parentApp.myPath = select_file 
        self.parent.update_grid()
        self.edit_cell = [0, 0]
        self.begin_row_display_at = 0
        self.begin_col_display_at = 0
        return True
 
    def h_select_file(self, *args, **keywrods):
        try:
             select_file = os.path.join(self.parent.value, self.values[self.edit_cell[0]][self.edit_cell[1]])
             select_file = os.path.abspath(select_file)
        except (TypeError, IndexError):
            self.edit_cell = [0, 0]
            return False
        
        if os.path.isdir(select_file):
            self.change_dir(select_file)
        else:
            mime = magic.from_file(select_file, mime=True)
            if mime == "text/plain":
                self.parent.parentApp.myFile = select_file
                self.parent.parentApp.switchForm("TEXTVIEWER")
            elif mime == 'image/png' or mime == "image/jpeg":
                self.parent.parentApp.myFile = select_file
                self.parent.parentApp.switchForm("IMGVIEWER")

    def delete_file(self, key):
        select_file = ""
        try:
             select_file = os.path.join(self.parent.value, self.values[self.edit_cell[0]][self.edit_cell[1]])
             select_file = os.path.abspath(select_file)
        except (TypeError, IndexError):
            return

        if not os.path.isfile(select_file):
            return

        self.parent.parentApp.myFile = select_file
        self.parent.parentApp.switchForm("DELETEFILE")

    def display_value(self, vl):
        p = os.path.split(vl)
        #File
        if p[1]:
            return p[1]
        #one up
        elif vl == ".." + os.sep:
            return os.path.split(p[0])[1] + os.sep
        #Subdirectory
        else:
            name = os.path.split(p[0])[1] + os.sep
            padding = max(int(self.width/2) - len(name), 1)
            f, d = directory_stats(vl)
            return name + " "*padding + "{} files, {} directories".format(f,d)

class FileBrowser(npyscreen.FormMuttActiveTraditional):
    ACTION_CONTROLLER = ActionController
    MAIN_WIDGET_CLASS = FileGrid
#    MAIN_WIDGET_CLASS_START_LINE = 30
#    BLANK_LINES_BASE = 0
    def __init__(self, *args, **keywords):
        super(FileBrowser, self).__init__(*args, **keywords)
        self.value = self.parentApp.myPath
        if not os.path.isdir(self.value):
            self.value = SFTP_ROOT_DIR

        if not os.path.isdir(SFTP_ROOT_DIR):
            os.mkdir(SFTP_ROOT_DIR)
        self.sort_by_extension = False

    def beforeEditing(self,):
        self.keypress_timeout = 80
        self.update_grid()
        self.stats_update()
        self.add_handlers({
            curses.KEY_BACKSPACE: self.parentApp.switchFormPrevious,
        })

    def reset_cursor(self):
        self.wMain.h_show_beginning('')

    def stats_update(self):
        self.wStatus2.value = "%s Bits connected at tick %s " % (
            get_connected_users(), datetime.now())

    def while_waiting(self):
        self.stats_update()
        self.update_grid()
        self.display()

    def update_grid(self,):
        #if self.value:
        #    self.value = os.path.expanduser(self.value)

        self.value = self.parentApp.myPath

        if not self.value.startswith(SFTP_ROOT_DIR):
            self.value = SFTP_ROOT_DIR
 
        if not os.path.exists(self.value):
            self.value = SFTP_ROOT_DIR 
            
        self.value = os.path.abspath(self.value)

        if os.path.isdir(self.value):
            working_dir = self.value + os.sep
        else:
            working_dir = os.path.dirname(self.value) + os.sep
            
        self.wStatus1.value = working_dir[len(os.path.abspath(SFTP_ROOT_DIR)):]
        #self.wStatus2.value = "sftp {}:{}".format(HOSTNAME,working_dir[len(os.path.abspath(SFTP_ROOT_DIR)):])

        file_list = []
        if not os.path.abspath(SFTP_ROOT_DIR) == os.path.abspath(self.value):
            file_list.append("..")

        try:
            file_list.extend([os.path.join(working_dir, fn) for fn in os.listdir(working_dir)])
        except OSError:
            npyscreen.notify_wait(title="Error", message="Could not read specified directory.")

        new_file_list = []
        for f in file_list:
            f = os.path.normpath(f)
            if os.path.isdir(f):
                new_file_list.append(f + os.sep)
            else:
                new_file_list.append(f) # + "*")
        file_list = new_file_list
        del new_file_list

        # sort Filelist
        file_list.sort()
        if self.sort_by_extension:
            file_list.sort(key=self.get_extension)
        file_list.sort(key=os.path.isdir, reverse=True)
        
        self.wMain.set_grid_values_from_flat_list(file_list, reset_cursor=False)
        
        self.display()
