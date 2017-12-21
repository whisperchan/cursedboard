#!/usr/bin/env python3
import sys
import subprocess
import curses
import re
import textwrap
import os

from datetime import datetime

import npyscreen
import GeoIP

from config import *
from database import Database
from motd import MotdPager, MOTD

HELP_TEXT = """
Navigate with arrow keys, j, k and <tab>. Confirm with enter or space. Go back up with backspace.
These vim style commands can be issued with : as prefix:


h, help      - This message
rules        - Show info
about
info

p, post      - Open the post form on a board
r, reply     - Open the reply form on a thread
b, board     - Go back to a board from thread
l, list      - Go back to overview
q, quit      - Jack out


auth         - Play god 
admin
       create     - Create a board
       delete     - Delete a post
       nuke       - Nuke a board
"""

RULES_TEXT = """
Decency is appreciated. That's all.

You can country ball on /int/.

You can make *text* bold and
>>1
>neurosuggest that this was a good idea

Keeping a board or thread open will refresh on new posts.
 
                 S T A Y  C O M F Y 

       and listen to the whispering machines


/cyb/erspace   for technology, security, culture, etc.
/meat/space    for cooking, diy, gardening,  etc.
/prog/gramming for all discussions around programming.
/int/national  country balling like in the old days.
/b/            everything else and quality shit posts.
/meta/         for all your nagging needs.

"""

def blockify(text, width, count):
    lines = textwrap.wrap(text, width)
    return lines[:count]


def padr(string, size):
    return str(string)+" "* (size-len(str(string)))

def padl(string, size):
    return " "* (size-len(str(string))) + str(string)

def get_connected_users():
    p = subprocess.Popen(["w", UNIX_USER, "-s"], stdout=subprocess.PIPE)
    out = p.communicate()[0]
    if out is None:
        return 0

    return len(out.decode().split("\n"))-3

def prettydate(created):
    if created == "":
        return "Never"

    now = datetime.now()
    posted = datetime.strptime(created, "%Y-%m-%d %H:%M:%S")
    diff = now-posted

    if diff.days < 0:
        return ''

    if diff.days == 0:
        if diff.seconds < 10:
            return "just now"
        if diff.seconds < 60:
            return str(diff.seconds) + " seconds ago"
        if diff.seconds < 120:
            return "a minute ago"
        if diff.seconds < 3600:
            return str(int(diff.seconds / 60)) + " minutes ago"
        if diff.seconds < 7200:
            return "an hour ago"
        if diff.seconds < 86400:
            return str(int(diff.seconds / 3600)) + " hours ago"

    if diff.days == 1:
        return "Yesterday"
    if diff.days < 7:
        return str(diff.days) + " days ago"
    if diff.days == 1:
        return "1 day ago"
    if diff.days < 14:
        return "1 week ago"
    if diff.days < 31:
        return str(int(diff.days / 7)) + " weeks ago"
    if diff.days < 365:
        return str(int(diff.days / 30)) + " months ago"
    return str(int(diff.days / 365)) + " years ago"

def update_highlighting(self, start=None, end=None, clear=False):
    value = self.display_value(self.value)
    # highlighting color
    normal = self.parent.theme_manager.findPair(self, 'DEFAULT')
    yellow = self.parent.theme_manager.findPair(self, 'WARNING')
    cyan = self.parent.theme_manager.findPair(self, 'STANDOUT')
    green = self.parent.theme_manager.findPair(self, 'SAFE')
    blue = self.parent.theme_manager.findPair(self, 'NO_EDIT')
    red = self.parent.theme_manager.findPair(self, 'DANGER')

    if value[:5] == "│ No.":
        color = []
        color += [normal]*2
        color += [yellow]*4
        color += [yellow | curses.A_BOLD] * MAX_POSTID_LENGTH
        color += [normal]*2
        color += [normal | curses.A_BOLD] * MAX_CHARS_TITLE
        color += [normal] * 2
        color += [cyan] * MAX_CHARS_NAME
        color += [normal]*22
        color += [red]*80
    else:
        if value[:3] == "│ >":
            color = [normal]*2+[green]*(len(value)-2)
        elif value[0] == ">":
            color = [green]*(len(value))
        else:
            color = [normal]*len(value)

        #bold
        p = re.compile("\*[a-zA-Z0-9!+-.,=']+\*")
        for m in p.finditer(value):
            s = m.span()
            for i in range(s[0], s[1]):
                color[i] |= curses.A_BOLD

        #post reference
        p = re.compile(">>[0-9]+")
        for m in p.finditer(value):
            s = m.span()
            for i in range(s[0], s[1]):
                color[i] = blue | curses.A_BOLD

    self._highlightingdata = color

class TextfieldHighlight(npyscreen.Textfield):
    def __init__(self, *args, **keywords):
        super(TextfieldHighlight, self).__init__(*args, **keywords)
        self.syntax_highlighting = True

    def update_highlighting(self, start=None, end=None, clear=False):
        update_highlighting(self, start, end)


class PagerHighlight(npyscreen.Pager):
    _contained_widgets = TextfieldHighlight 


class PopupBig(npyscreen.ActionFormMinimal):
        DEFAULT_LINES = 30
        DEFAULT_COLUMNS = 60
        SHOW_ATX = 10
        SHOW_ATY = 2

def _wrap_message_lines(message, line_length):
    lines = []
    for line in message.split('\n'):
        if len(line) == 0:
            lines.append('')
            continue
        lines.extend(textwrap.wrap(line.rstrip(), line_length))
    return lines
    
def cursed_notify(message, title="Message", form_color='STANDOUT', editw = 0,):
    F = PopupBig(name=title, color=form_color)
    F.preserve_selected_widget = True
    mlw = F.add(PagerHighlight,)
    mlw_width = mlw.width-1
    mlw.values = _wrap_message_lines(message, mlw_width)
    F.editw = editw
    F.edit()





class ActionController(npyscreen.ActionControllerSimple):
    def create(self):
        self.add_action('^:.*', self.execute_command, False)

        self.CMD = {
            'p': self.post,
            'post': self.post,
            'r': self.reply,
            'reply': self.reply,
            'b': self.current_board,
            'board': self.current_board,
            'l': self.list,
            'list': self.list,
            'q': self.quit,
            'quit': self.quit,
            'admin': self.admin,
            'h': self.help,
            'help': self.help,
            'rules': self.rules,
            'info': self.rules,
            'about': self.rules,
            'auth'  : self.auth,
        }

        self.ADMIN = {
            'create': self.create_board,
            'delete': self.delete_post,
            'nuke'  : self.nuke_board,
        }

    def set_search(self, command_line, widget_proxy, live):
        self.parent.value.set_filter(command_line[1:])
        self.parent.wMain.values = self.parent.value.get()
        self.parent.wMain.display()

    def execute_command(self, command_line, widget_proxy, live):
        command_line = command_line[1:]
        command_line = command_line.split(" ")

        cmd = self.CMD.get(command_line[0], self.unknown_command)
        self.parent.wStatus2.value = ""

        cmd(*command_line)
        self.parent.display()
        self.parent.wMain.display()

    def unknown_command(self, *args):
        self.parent.wStatus2.value = "Unknown Command %s" % args[0]

    def quit(self, *args):
        self.parent.parentApp.switchForm(None)

    def admin(self, *args):
        if not self.parent.parentApp.admin:
            self.parent.wStatus2.value = "Not an admin"
            return

        if len(args) == 1:
            self.parent.wStatus2.value = "No command after admin"
            return

        cmd = self.ADMIN.get(args[1], self.unknown_command)
        cmd(*args[2:])

    def current_board(self, *args):
        self.parent.parentApp.myThreadId = 0
        self.parent.parentApp.switchForm("BOARD")

    def list(self, *args):
        self.parent.parentApp.myThreadId = 0
        self.parent.parentApp.myBoardId = 0
        self.parent.parentApp.switchForm("MAIN")

    def auth(self, *args):
        if args is None or len(args) < 1:
            self.parent.wStatus2.value = "admin auth <password>"
            return

        self.parent.parentApp.authenticate(args[1])

        if self.parent.parentApp.authenticated():
            self.parent.wStatus2.value = "God Mode enabled"
        else:
            self.parent.wStatus2.value = "Denied"


    def create_board(self, *args):
        if args is None or len(args) < 3:
            self.parent.wStatus2.value = "admin create <name> <countryballs> <description>"
            return


        name = args[0]
        country_balls = args[1]
        description = " ".join(args[2:])
        self.parent.parentApp.myDatabase.create_board(name, description,country_balls)
        self.parent.parentApp.switchForm('MAIN')

    def delete_post(self, *args):
        if args is None or len(args) < 1:
            self.parent.wStatus2.value = "admin delete <postid>"
            return

        if self.parent.parentApp._THISFORM.FORM_NAME != "THREAD":
            self.parent.wStatus2.value = "Not in a thread"
            return

        self.parent.parentApp.myDatabase.delete_post(self.parent.parentApp.myBoardId, args[0])
        self.parent.parentApp.switchForm("THREAD")

    def nuke_board(self, *args):
        if args is None or len(args) < 1:
            self.parent.wStatus2.value = "admin nuke <name>"
            return

        if self.parent.parentApp._THISFORM.FORM_NAME != "MAIN":
            self.parent.wStatus2.value = "Not in list"
            return

        boardid = self.parent.parentApp.myDatabase.name_to_bid(args[0])

        if boardid is None:
            self.parent.wStatus2.value = "Board not found"
            return

        boardid = boardid[0]

        self.parent.parentApp.myDatabase.nuke_board(boardid)
        self.parent.parentApp.switchForm("MAIN")

    def post(self, *args):
        if self.parent.parentApp._THISFORM.FORM_NAME != "BOARD":
            self.parent.wStatus2.value = "Not on a board"
            return

        self.parent.parentApp.switchForm("POST")

    def reply(self, *args):
        #can be made context aware
        if self.parent.parentApp._THISFORM.FORM_NAME != "THREAD":
            self.parent.wStatus2.value = "Not in a thread"
            return

        self.parent.parentApp.switchForm("POST")


    def help(self, *args):
        cursed_notify(HELP_TEXT, title="Help")

    def rules(self, *args):
        placard = RULES_TEXT
        cursed_notify(placard, title="House Rules")




class BoardList(npyscreen.MultiLineAction):
    def display_value(self, value):
        return "%s %s ticked %s" % (padr("/%s/" %(value[1]), 10), padr(value[2], 40), prettydate(value[3]))

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
                                height=self.__class__.MAIN_WIDGET_CLASS_START_LINE-1,
                                relx=self.__class__.STATUS_WIDGET_X_OFFSET,
                                editable=False)

        self.wStatus1 = self.add(self.__class__.STATUS_WIDGET_CLASS,
                                rely=self.__class__.MAIN_WIDGET_CLASS_START_LINE-1,
                                relx=self.__class__.STATUS_WIDGET_X_OFFSET,
                                editable=False)

        self.wMain = self.add(self.__class__.MAIN_WIDGET_CLASS,
                                rely=self.__class__.MAIN_WIDGET_CLASS_START_LINE,
                                relx=0, max_height=-2, allow_filtering=False)

        self.wStatus2 = self.add(self.__class__.STATUS_WIDGET_CLASS, rely=MAXY-2-self.BLANK_LINES_BASE,
                                relx=self.__class__.STATUS_WIDGET_X_OFFSET,
                                editable=False)

        self.wCommand = self.add(self.__class__.COMMAND_WIDGET_CLASS, name=self.__class__.COMMAND_WIDGET_NAME,
                                rely=MAXY-1-self.BLANK_LINES_BASE, relx=0,
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
        self.wStatus2.value = "%s Bits conntected at tick %s " %(get_connected_users(), datetime.now())
        self.wMain.values = self.parentApp.myDatabase.get_boards()


class ThreadLine(npyscreen.Textfield):
    def __init__(self, *args, **keywords):
        super(ThreadLine, self).__init__(*args, **keywords)
        self.syntax_highlighting = True

    def update_highlighting(self, start=None, end=None, clear=False):
        update_highlighting(self, start, end)


class ThreadPager(npyscreen.Pager):
    _contained_widgets = ThreadLine


class ThreadView(npyscreen.FormMuttActiveTraditional):
    MAIN_WIDGET_CLASS = ThreadPager
    ACTION_CONTROLLER = ActionController

    def beforeEditing(self):
        self.wStatus1.value = "Thread View "
        self.wStatus2.value = ""
        threads = self.parentApp.myDatabase.get_thread(self.parentApp.myBoardId, self.parentApp.myThreadId)
        self.wMain.values = threads
        self.keypress_timeout = 80


        self.update_list()
        self.stats_update()
        self.add_handlers({
                    curses.KEY_BACKSPACE: self.action_controller.current_board,
                }) 

    def stats_update(self):
        self.wStatus2.value = "%s Bits conntected at tick %s " %(get_connected_users(), datetime.now())

    def while_waiting(self):
        self.stats_update()
        threads = self.parentApp.myDatabase.get_thread(self.parentApp.myBoardId, self.parentApp.myThreadId)
        self.wMain.values = threads
        self.update_list()
        self.display()

    def update_list(self):
        threads = self.parentApp.myDatabase.get_thread(self.parentApp.myBoardId, self.parentApp.myThreadId)
        if len(threads) == 0:
            self.parentApp.switchForm('BOARD')
            return

        text = ""
        self.wStatus1.value = "Thread No. %s - %s " %(padr(threads[0]['pid'], MAX_POSTID_LENGTH), padr(threads[0]['title'], 10))
        self.wMain.values = threads
        for thread in threads:
            text += "┌"+"─"*85+"\n"
            text += "│ No. %s " %(padl(thread['pid'], MAX_POSTID_LENGTH))
            text += " %s  %s " %(padr(thread['title'], MAX_CHARS_TITLE), padr(thread['name'], MAX_CHARS_NAME))
            text += "  %s %s\n│\n" %(thread['created'], thread['country'])

            lines = 0
            for line in thread['content'].split("\n"):
                text += "│ " + line +"\n"
                lines += 1

            if lines < 10:
                text += "│\n"*(10-lines)

            text += "\n"

        self.wMain.values = text.split("\n")



class BoardThreadLine(npyscreen.Textfield):
    def __init__(self, *args, **keywords):
        super(BoardThreadLine, self).__init__(*args, **keywords)
        self.syntax_highlighting = True

    def update_highlighting(self, start=None, end=None, clear=False):
        value = self.display_value(self.value)
        highlight = self.my_selected*curses.A_BOLD 
        normal = self.parent.theme_manager.findPair(self, 'DEFAULT') | highlight
        yellow = self.parent.theme_manager.findPair(self, 'WARNING')| highlight
        cyan = self.parent.theme_manager.findPair(self, 'STANDOUT')| highlight
        green = self.parent.theme_manager.findPair(self, 'SAFE')| highlight
        blue = self.parent.theme_manager.findPair(self, 'NO_EDIT')| highlight
        red = self.parent.theme_manager.findPair(self, 'DANGER')| highlight

        posts = re.search("^│ ([0-9])+ Posts", value)

        if value[:5] == "│ No.":
            color = []
            color += [normal]*2
            color += [yellow]*4
            color += [yellow | curses.A_BOLD] * MAX_POSTID_LENGTH
            color += [normal]*2
            color += [normal | curses.A_BOLD] * MAX_CHARS_TITLE
            color += [normal] * 2
            color += [cyan] * MAX_CHARS_NAME
            color += [normal]*20
            color += [red]*80

        elif value[:7] == "│   No.":
            color = []
            color += [normal]*4
            color += [yellow]*4
            color += [yellow | curses.A_BOLD] * MAX_POSTID_LENGTH
            color += [normal]*2
            color += [normal | curses.A_BOLD] * MAX_CHARS_TITLE
            color += [normal] * 2
            color += [cyan] * MAX_CHARS_NAME
            color += [normal]*20
            color += [red]*80

        elif posts:
            color = []
            color += [normal]*2 
            color += [blue | curses.A_BOLD] * len(posts.groups()[0])
            color += [blue]*16

        elif value[:6] == "│ No R":
            color = [normal]*2
            color += [blue]*20

        elif False:
            if value[:3] == "│ >":
                color = [normal]*2+[green]*(len(value)-2)
            elif value[0] == ">":
                color = [green]*(len(value))
            else:
                color = [normal]*len(value)

            #bold
            p = re.compile("\*[a-zA-Z0-9!+-.,=']+\*")
            for m in p.finditer(value):
                s = m.span()
                for i in range(s[0], s[1]):
                    color[i] |= curses.A_BOLD

            #post reference
            p = re.compile(">>[0-9]+")
            for m in p.finditer(value):
                s = m.span()
                for i in range(s[0], s[1]):
                    color[i] = blue | curses.A_BOLD
        else:
            color = [normal]*(end-start)

        self._highlightingdata = color


class BoardThread(npyscreen.Pager):
    _contained_widgets = BoardThreadLine
    def update(self, clear=True):
        for w in self._my_widgets:
            w.my_selected = self.highlight
        super(BoardThread,self).update(clear=clear)

    def display_value(self, value):
        if not self.hidden:
            return value
        return None


class Board(npyscreen.MultiLineAction):
    _contained_widgets = BoardThread
    _contained_widget_height = THREAD_PREVIEW_HEIGHT
    def display_value(self, value):
        first = value['first']
        last = value['last']

        text = "┌"+"─"*85+"\n"
        text += "│ No. %s  %s  %s %s %s                              \n"  % (padl(first['pid'], MAX_POSTID_LENGTH),
                                            padr(first['title'], MAX_CHARS_TITLE),
                                            padr(first['name'], MAX_CHARS_NAME),
                                            first['created'], first['country'])
        blocks = blockify(first['content'], self.width-8, 3)

        for line in blocks:
            text += "│    "+line + "\n"   
        text += "│\n"*(3-len(blocks))
 
        if first['pid'] == last['pid']:
            text += "│ No Replies \n│\n│\n│\n│\n│\n"
            return text.split("\n")


        text += "│ %s Posts hidden\n" %(value['posts']-2)
        text += "│   No. %s  %s  %s %s %s                             \n" % (padl(last['pid'], MAX_POSTID_LENGTH),
                                            padr(last['title'], MAX_CHARS_TITLE),
                                            padr(last['name'], MAX_CHARS_NAME),
                                            last['created'], last['country'])

        blocks = blockify(last['content'], self.width-10, 3)

        for line in blocks:
            text += "│       "+line + "\n"
        text += "│\n"*(3-len(blocks))

        return text.split("\n")

    def _set_line_values(self, line, value_indexer):
        try:
            _vl = self.values[value_indexer]
        except IndexError:
            self._set_line_blank(line)
            return False
        except TypeError:
            self._set_line_blank(line)
            return False
        line.values = self.display_value(_vl)
        line.hidden = False

    def actionHighlighted(self, value, keypress):
        self.parent.parentApp.myThreadId = value['first']['pid']
        self.parent.parentApp.switchForm('THREAD')

class BoardView(npyscreen.FormMuttActiveTraditional):
    ACTION_CONTROLLER = ActionController
    MAIN_WIDGET_CLASS = Board
    def create(self, *args, **keywords):
        MAXY = self.lines
        self.wStatus1 = self.add(self.__class__.STATUS_WIDGET_CLASS,
                                rely=self.__class__.MAIN_WIDGET_CLASS_START_LINE-1,
                                relx=self.__class__.STATUS_WIDGET_X_OFFSET,
                                editable=False)

        self.wMain = self.add(self.__class__.MAIN_WIDGET_CLASS,
                                rely=self.__class__.MAIN_WIDGET_CLASS_START_LINE,
                                relx=0, max_height=-2, allow_filtering=False)

        self.wStatus2 = self.add(self.__class__.STATUS_WIDGET_CLASS, rely=MAXY-2-self.BLANK_LINES_BASE,
                                relx=self.__class__.STATUS_WIDGET_X_OFFSET,
                                editable=False)

        self.wCommand = self.add(self.__class__.COMMAND_WIDGET_CLASS, name=self.__class__.COMMAND_WIDGET_NAME,
                                rely=MAXY-1-self.BLANK_LINES_BASE, relx=0,
                                begin_entry_at=True,
                                allow_override_begin_entry_at=True)
        self.wStatus1.important = True
        self.wStatus2.important = True
        self.nextrely = 2
        self.keypress_timeout = 80
        self.add_handlers({
                    curses.KEY_BACKSPACE: self.action_controller.list,
                }) 

    def beforeEditing(self):
        board = self.parentApp.myDatabase.get_board(self.parentApp.myBoardId)
        self.wStatus1.value = "/%s/ - %s " % board
        self.wStatus2.value = ""
        self.wMain.values = self.parentApp.myDatabase.get_threads(self.parentApp.myBoardId)
        self.parentApp.myThreadTitle = ""
        self.parentApp.myThreadContent = ""

        self.stats_update()

    def stats_update(self):
        self.wStatus2.value = "%s Bits conntected at tick %s " %(get_connected_users(), datetime.now())

    def while_waiting(self):
        self.stats_update()
        self.wMain.values = self.parentApp.myDatabase.get_threads(self.parentApp.myBoardId)
        self.display()

class MaxTitleTextfield(npyscreen.Textfield):
    def __init__(self, *args, **keywords):
        self.max_length = int(keywords['max_length'])
        super(MaxTitleTextfield, self).__init__(*args, **keywords)

    def h_addch(self, inp):
        if len(self.value) < self.max_length:
            return super(MaxTitleTextfield, self).h_addch(inp)
        return

class MaxTitleText(npyscreen.TitleText):
    _entry_type = MaxTitleTextfield

class MaxMultiLineEdit(npyscreen.MultiLineEdit):
    def __init__(self, *args, **keywords):
        self.max_length = int(keywords['max_length'])
        self.max_lines = int(keywords['max_lines'])

        super(MaxMultiLineEdit, self).__init__(*args, **keywords)

    def h_addch(self, inp):
        if len(self.value) < self.max_length and self.value.count('\n') < self.max_lines :
            return super(MaxMultiLineEdit, self).h_addch(inp)
        return


class BoxedMaxMultiLineEdit(npyscreen.BoxTitle):
    _contained_widget = MaxMultiLineEdit

class PostForm(npyscreen.ActionPopup):
    CANCEL_BUTTON_BR_OFFSET = (2, 73)
    OK_BUTTON_TEXT = "Post!"
    CANCEL_BUTTON_TEXT = "Cancel"
    DEFAULT_LINES = 31
    DEFAULT_COLUMNS = 80
    def create(self):
        self.value = None
        self.wgTitle = self.add(MaxTitleText, name="Title:", max_length=MAX_CHARS_TITLE)
        self.wgName = self.add(MaxTitleText, name="Name:", max_length=MAX_CHARS_NAME)
        self.wgContent = self.add(BoxedMaxMultiLineEdit, name="Post", max_height=23, contained_widget_arguments={'max_length':MAX_CHARS_POST, 'max_lines':MAX_LINES_POST})
        self.wgFooter = self.add(npyscreen.FixedText)
        self.wCancel = self.add(npyscreen.MiniButtonPress, name="Hide", when_pressed_function=self.on_hide)

    def beforeEditing(self):
        self.wgTitle.value = ""
        self.wgName.value = ANON_NAME
        self.wgContent.value = ""
        if self.parentApp._FORM_VISIT_LIST[-2] == "THREAD":
            self.wgFooter.value = "              Hiding will keep the form content in the thread"
            self.wgTitle.value = self.parentApp.myThreadTitle
            self.wgContent.value = self.parentApp.myThreadContent

    def on_ok(self):
        if len(self.wgContent.value) < MIN_CHARS_POST:
            npyscreen.notify_wait("Not enough Content", title='You failed')
            return

        self.parentApp.myThreadTitle = ""
        self.parentApp.myThreadContent = ""

        country = ""
        if self.parentApp.authenticated():
            country = "##BOT##"
        elif self.parentApp.myDatabase.board_has_country_balls(self.parentApp.myBoardId):
            gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)
            ip = os.getenv("SSH_CLIENT")
            if not ip:
                country = "Onion"
            else:
                ip = ip.split(" ")[0]
                country = gi.country_name_by_addr(ip)


        self.parentApp.myDatabase.post(self.parentApp.myBoardId, self.parentApp.myThreadId, self.wgName.value, self.wgTitle.value, self.wgContent.value, country)
        self.parentApp.switchFormPrevious()

    def on_cancel(self):
        self.parentApp.myThreadTitle   = ""
        self.parentApp.myThreadContent = ""
        self.parentApp.switchFormPrevious()

    def on_hide(self):
        if self.parentApp._FORM_VISIT_LIST[-2] == "THREAD":
            self.parentApp.myThreadTitle   = self.wgTitle.value
            self.parentApp.myThreadContent = self.wgContent.value
        else:
            self.parentApp.myThreadTitle   = ""
            self.parentApp.myThreadContent = ""

        self.parentApp.switchFormPrevious()



class TestApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.admin = False
        self.myDatabase = Database(filename=DATABASE_FILE)
        self.myBoardId = 1
        self.myThreadId = 0
        self.myThreadTitle = ""
        self.myThreadContent = ""
        self.addForm("MAIN", Frontpage)
        self.addForm("BOARD", BoardView)
        self.addForm("POST", PostForm)
        self.addForm("THREAD", ThreadView)
        #Disable mouse, easier copy / paste
        curses.mousemask(0)
    def authenticate(self, pw):
        self.admin = False
        if pw == PASSWORD:
            self.admin = True

    def authenticated(self):
        return self.admin


if __name__ == "__main__":
        try:
            App = TestApp()
            App.run()
        except npyscreen.wgwidget.NotEnoughSpaceForWidget:
            print("Please increase the size of your terminal and reconnect")
        except KeyboardInterrupt:
            print("Good bye")
