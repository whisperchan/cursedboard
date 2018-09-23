#!/usr/bin/env python3
import npyscreen
import session
import curses
import sys

from config import *
from database import Database
from thread_view import ThreadView
from frontpage import Frontpage
from board_view import BoardView
from post_form import PostForm
from file_browser import FileBrowser, TextViewer, DeleteFileForm
from image_viewer import ImageViewer

class TestApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.admin = False
        self.myDatabase = Database(filename=DATABASE_FILE)
        self.myBoardId = 0
        self.myThreadId = 0
        self.myThreadTitle = ""
        self.myThreadContent = ""
        self.myPath = ""
        self.addForm("MAIN", Frontpage)
        self.addForm("BOARD", BoardView)
        self.addForm("POST", PostForm)
        self.addForm("THREAD", ThreadView)
        self.addForm("FILES", FileBrowser)
        self.addForm("TEXTVIEWER", TextViewer)
        self.addForm("IMGVIEWER", ImageViewer)
        self.addForm("DELETEFILE", DeleteFileForm)
        # Disable mouse, easier copy / paste
        curses.mousemask(0)

    def authenticate(self, pw):
        self.admin = False
        if pw == PASSWORD:
            self.admin = True

    def authenticated(self):
        return self.admin


if __name__ == "__main__":
    try:
        if len(sys.argv) == 2:
            session.parse_session(sys.argv[1])

        App = TestApp()
        App.run()
    except npyscreen.wgwidget.NotEnoughSpaceForWidget:
        print("Please increase the size of your terminal and reconnect")
        print("Press any key to close connection")
        input()
    except KeyboardInterrupt:
        print("Good bye")
