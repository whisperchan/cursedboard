#!/usr/bin/env python3
import curses
import re
import textwrap
import os
import glob
import random

from datetime import datetime

import npyscreen

from config import *
from utils import *
from database import Database
from controller import ActionController


class ThreadLine(npyscreen.Textfield):
    def __init__(self, *args, **keywords):
        super(ThreadLine, self).__init__(*args, **keywords)
        self.syntax_highlighting = True

    def update_highlighting(self, start=None, end=None, clear=False):
        update_highlighting(self, start, end)


class ThreadPager(npyscreen.Pager):
    _contained_widgets = ThreadLine
    def __init__(self, *args, **keywords):
        super(ThreadPager, self).__init__(*args, **keywords)
        self.handlers.update({
            curses.KEY_LEFT: self.parent.action_controller.current_board,
        })


class ThreadView(npyscreen.FormMuttActiveTraditional):
    MAIN_WIDGET_CLASS = ThreadPager
    ACTION_CONTROLLER = ActionController

    def beforeEditing(self):
        self.wStatus1.value = "Thread View "
        self.wStatus2.value = ""
        threads = self.parentApp.myDatabase.get_thread(
            self.parentApp.myBoardId, self.parentApp.myThreadId)
        self.wMain.values = threads
        self.keypress_timeout = 80

        self.update_list()
        self.stats_update()
        self.add_handlers({
            curses.KEY_BACKSPACE: self.action_controller.current_board,
        })

    def stats_update(self):
        self.wStatus2.value = "%s Bits conntected at tick %s " % (
            get_connected_users(), datetime.now())

    def while_waiting(self):
        self.stats_update()
        threads = self.parentApp.myDatabase.get_thread(
            self.parentApp.myBoardId, self.parentApp.myThreadId)
        self.wMain.values = threads
        self.update_list()
        self.display()

    def update_list(self):
        threads = self.parentApp.myDatabase.get_thread(
            self.parentApp.myBoardId, self.parentApp.myThreadId)
        if len(threads) == 0:
            self.parentApp.switchForm('BOARD')
            return

        text = ""
        self.wStatus1.value = "Thread No. %s - %s " % (
            padr(threads[0]['pid'], MAX_POSTID_LENGTH), padr(threads[0]['title'], 10))
        self.wMain.values = threads
        for thread in threads:
            text += "┌" + "─" * 85 + "\n"
            text += "│ No. %s " % (padl(thread['pid'], MAX_POSTID_LENGTH))
            text += " %s  %s " % (padr(thread['title'], MAX_CHARS_TITLE),
                                  padr(thread['name'], MAX_CHARS_NAME))
            text += "  %s %s\n" % (thread['created'], thread['country'])

            if SFTP_INTEGRATION:
                files = self.get_files_for_post(thread['pid'], thread['tid'])
                if len(files):
                    for line in blockify(" ".join(files), self.wMain.width, 5):
                        text += "│ Attached: {}\n".format(line)
            text += "│\n"
            lines = 0
            for line in thread['content'].split("\n"):
                text += "│ " + line + "\n"
                lines += 1

            if lines < 10:
                text += "│\n" * (10 - lines)

            text += "\n"

        self.wMain.values = text.split("\n")

    def get_files_for_post(self, pid, tid):
        thread_path = get_local_path(self.parentApp.myDatabase, self.parentApp.myBoardId, tid)
        if not os.path.isdir(thread_path):
            return []

        files = os.listdir(thread_path)
        return [name for name in files if re.match("{}_.*".format(pid), name)] 
