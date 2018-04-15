import npyscreen
import curses

from config import *
from utils import *
from motd import MotdPager, MOTD
from controller import ActionController, HELP_TEXT

class BoardList(npyscreen.MultiLineAction):
    def __init__(self, *args, **keywords):
        super(BoardList, self).__init__(*args, **keywords)

        del self.handlers[curses.KEY_LEFT]

        self.handlers.update({
            curses.KEY_RIGHT: self.h_act_on_highlighted,
        })

    def display_value(self, value):
        return "%s %s ticked %s" % (padr("/%s/" % (value[1]), 10), padr(value[2], 40), prettydate(value[3]))

    def actionHighlighted(self, value, keypress):
        self.parent.parentApp.myBoardId = int(value[0])
        self.parent.parentApp.switchForm('BOARD')


class Frontpage(npyscreen.FormMuttActiveTraditional):
    ACTION_CONTROLLER = ActionController
    MAIN_WIDGET_CLASS = BoardList
    MAIN_WIDGET_CLASS_START_LINE = 30
    BLANK_LINES_BASE = 0

    def create(self, *args, **keywords):
        MAXY = self.lines
        self.wMotd = self.add(MotdPager, values=MOTD.split("\n"), rely=0,
                              height=self.__class__.MAIN_WIDGET_CLASS_START_LINE - 1,
                              relx=self.__class__.STATUS_WIDGET_X_OFFSET,
                              editable=False)

        self.wStatus1 = self.add(self.__class__.STATUS_WIDGET_CLASS,
                                 rely=self.__class__.MAIN_WIDGET_CLASS_START_LINE - 1,
                                 relx=self.__class__.STATUS_WIDGET_X_OFFSET,
                                 editable=False)

        self.wMain = self.add(self.__class__.MAIN_WIDGET_CLASS,
                              rely=self.__class__.MAIN_WIDGET_CLASS_START_LINE,
                              relx=0, max_height=-2, allow_filtering=False)

        self.wStatus2 = self.add(self.__class__.STATUS_WIDGET_CLASS, rely=MAXY - 2 - self.BLANK_LINES_BASE,
                                 relx=self.__class__.STATUS_WIDGET_X_OFFSET,
                                 editable=False)

        self.wCommand = self.add(self.__class__.COMMAND_WIDGET_CLASS, name=self.__class__.COMMAND_WIDGET_NAME,
                                 rely=MAXY - 1 - self.BLANK_LINES_BASE, relx=0,
                                 begin_entry_at=True,
                                 allow_override_begin_entry_at=True)
        self.wStatus1.important = True
        self.wStatus2.important = True
        self.nextrely = 2
        self.keypress_timeout = 20

        self.add_handlers({
            'h': self.display_help,
            'H': self.display_help
        })

    def display_help(self, *args, **keywords):
        cursed_notify(HELP_TEXT, title="Help")

    def while_waiting(self):
        self.stats_update()
        self.display()

    def beforeEditing(self):
        self.wStatus1.value = "Boards"
        self.stats_update()

    def stats_update(self):
        self.wStatus2.value = "%s Bits connected at tick %s " % (
            get_connected_users(), datetime.now())
        self.wMain.values = self.parentApp.myDatabase.get_boards()

