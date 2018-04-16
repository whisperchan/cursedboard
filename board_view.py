import npyscreen
import curses

from config import *
from utils import *
from controller import ActionController

class BoardThreadLine(npyscreen.Textfield):
    def __init__(self, *args, **keywords):
        super(BoardThreadLine, self).__init__(*args, **keywords)
        self.syntax_highlighting = True

    def update_highlighting(self, start=None, end=None, clear=False):
        value = self.display_value(self.value)
        highlight = self.my_selected * curses.A_BOLD
        normal = self.parent.theme_manager.findPair(
            self, 'DEFAULT') | highlight
        yellow = self.parent.theme_manager.findPair(
            self, 'WARNING') | highlight
        cyan = self.parent.theme_manager.findPair(self, 'STANDOUT') | highlight
        green = self.parent.theme_manager.findPair(self, 'SAFE') | highlight
        blue = self.parent.theme_manager.findPair(self, 'NO_EDIT') | highlight
        red = self.parent.theme_manager.findPair(self, 'DANGER') | highlight

        posts = re.search("^│ ([0-9])+ Posts", value)

        if value[:5] == "│ No.":
            color = []
            color += [normal] * 2
            color += [yellow] * 4
            color += [yellow | curses.A_BOLD] * MAX_POSTID_LENGTH
            color += [normal] * 2
            color += [normal | curses.A_BOLD] * MAX_CHARS_TITLE
            color += [normal] * 2
            color += [cyan] * MAX_CHARS_NAME
            color += [normal] * 20
            color += [red] * 80

        elif value[:7] == "│   No.":
            color = []
            color += [normal] * 4
            color += [yellow] * 4
            color += [yellow | curses.A_BOLD] * MAX_POSTID_LENGTH
            color += [normal] * 2
            color += [normal | curses.A_BOLD] * MAX_CHARS_TITLE
            color += [normal] * 2
            color += [cyan] * MAX_CHARS_NAME
            color += [normal] * 20
            color += [red] * 80

        elif posts:
            color = []
            color += [normal] * 2
            color += [blue | curses.A_BOLD] * len(posts.groups()[0])
            color += [blue] * 16

        elif value[:6] == "│ No R":
            color = [normal] * 2
            color += [blue] * 20

        elif False:
            if value[:3] == "│ >":
                color = [normal] * 2 + [green] * (len(value) - 2)
            elif value[0] == ">":
                color = [green] * (len(value))
            else:
                color = [normal] * len(value)

            # bold
            p = re.compile("\*[a-zA-Z0-9!+-.,=']+\*")
            for m in p.finditer(value):
                s = m.span()
                for i in range(s[0], s[1]):
                    color[i] |= curses.A_BOLD

            # post reference
            p = re.compile(">>[0-9]+")
            for m in p.finditer(value):
                s = m.span()
                for i in range(s[0], s[1]):
                    color[i] = blue | curses.A_BOLD
        else:
            color = [normal] * (end - start)

        self._highlightingdata = color


class BoardThread(npyscreen.Pager):
    _contained_widgets = BoardThreadLine
    def update(self, clear=True):
        #Propagates to the line widgets that they should use BOLD
        for w in self._my_widgets:
            w.my_selected = self.highlight
        super(BoardThread, self).update(clear=clear)

    def display_value(self, value):
        if not self.hidden:
            return value
        return None


class Board(npyscreen.MultiLineAction):
    _contained_widgets = BoardThread
    _contained_widget_height = THREAD_PREVIEW_HEIGHT
    def __init__(self, *args, **keywords):
        super(Board, self).__init__(*args, **keywords)
        self.slow_scroll = True
        self.handlers.update({
            curses.KEY_RIGHT: self.h_act_on_highlighted,
            curses.KEY_LEFT: self.parent.action_controller.list,
        })

    def display_value(self, value):
        first = value['first']
        last = value['last']

        text = "┌" + "─" * 85 + "\n"
        text += "│ No. %s  %s  %s %s %s                               \n" % (padl(first['pid'], MAX_POSTID_LENGTH),
                                                                            padr(
                                                                                first['title'], MAX_CHARS_TITLE),
                                                                            padr(
                                                                                first['name'], MAX_CHARS_NAME),
                                                                            first['created'], first['country'])
        blocks = blockify(first['content'], self.width - 8, 3)

        for line in blocks:
            text += "│    " + line + "\n"
        text += "│\n" * (3 - len(blocks))

        if first['pid'] == last['pid']:
            text += "│ No Replies \n│\n│\n│\n│\n"
            return text.split("\n")

        text += "│ %s Posts hidden\n" % (value['posts'] - 2)
        text += "│   No. %s  %s  %s %s %s                             \n" % (padl(last['pid'], MAX_POSTID_LENGTH),
                                                                             padr(
                                                                                 last['title'], MAX_CHARS_TITLE),
                                                                             padr(
                                                                                 last['name'], MAX_CHARS_NAME),
                                                                             last['created'], last['country'])

        blocks = blockify(last['content'], self.width - 10, 3)

        for line in blocks:
            text += "│       " + line + "\n"
        text += "│\n" * (3 - len(blocks))

        return text.split("\n")

    def update(self, clear=True):
        # There is a edge case were it start_display_at becomes -1 when
        # posting on an empty board. This is 'solves' that problem
        self.start_display_at = max(self.start_display_at, 0)
        super(Board, self).update(clear)


        label = "Thread %s/%s " % (self.cursor_line+1, len(self.values))
        self.parent.curses_pad.addstr(self.rely+self.height-1, self.relx, label, self.parent.theme_manager.findPair(self, 'CONTROL'))


        #index of the value displayed when scrolled down one more
        index = self.start_display_at + len(self._my_widgets)

        # if there are no values left to display skip partial preview
        if index >= len(self.values) or len(self._my_widgets) >= len(self.values):
            return

        lines = self.height - ( len(self._my_widgets)*self._contained_widget_height)-1
        line_values = self.display_value(self.values[index])
        #fill up the rest of available lines with 'non-selectable' preview
        for i in range(0, min(lines, len(line_values))):
            self.parent.curses_pad.addstr(len(self._my_widgets)*self._contained_widget_height+i+self.rely,
                                            1,
                                            line_values[i],
                                            0)

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
        self.parent.parentApp.myThreadId = value['first']['tid']
        self.parent.parentApp.switchForm('THREAD')



class BoardView(npyscreen.FormMuttActiveTraditional):
    ACTION_CONTROLLER = ActionController
    MAIN_WIDGET_CLASS = Board
    MAIN_WIDGET_CLASS_START_LINE = 14

    def create(self, *args, **keywords):
        MAXY = self.lines
        self.wStatus1 = self.add(self.__class__.STATUS_WIDGET_CLASS,
                                 rely=0,
                                 relx=self.__class__.STATUS_WIDGET_X_OFFSET,
                                 editable=False)
        self.wBanner= self.add(npyscreen.Pager,
                                height = 13,
                                 rely=self.__class__.MAIN_WIDGET_CLASS_START_LINE - 13,
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
        self.keypress_timeout = 80
        self.add_handlers({
            curses.KEY_BACKSPACE: self.action_controller.list,
        })

        self.current_board = 0

    def beforeEditing(self):
        board = self.parentApp.myDatabase.get_board(self.parentApp.myBoardId)
        self.wStatus1.value = "/%s/ - %s " % board
        self.wStatus2.value = ""
        self.wMain.values = self.parentApp.myDatabase.get_threads(
            self.parentApp.myBoardId)
        self.parentApp.myThreadTitle = ""
        self.parentApp.myThreadContent = ""

        if self.current_board != self.parentApp.myBoardId:
            self.wMain.reset_cursor()
            self.current_board = self.parentApp.myBoardId

        self.stats_update()
        self.banner_update()

    def get_banner(self):
        base_dir = os.path.dirname(os.path.realpath(__file__))
        banners = glob.glob(base_dir+"/banners/default-*.banner")
        banners += glob.glob(base_dir+"/banners/%s-*.banner" %(self.parentApp.myBoardId))

        return open(random.choice(banners), "r").readlines()
     

    def banner_update(self): 
        banner = self.get_banner()
        # Center the banner
        pad = int((self.columns-len(max(banner, key=len)))/2)
        if pad < 0:
            pad = 0
        for i in range(0, len(banner)):
            banner[i] = " "*pad + banner[i]

        self.wBanner.values = banner

    def stats_update(self):
        self.wStatus2.value = "%s Bits connected at tick %s " % (
            get_connected_users(), datetime.now())

    def while_waiting(self):
        self.stats_update()
        self.banner_update()
        self.wMain.values = self.parentApp.myDatabase.get_threads(
            self.parentApp.myBoardId)
        self.display()
