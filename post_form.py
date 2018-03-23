import npyscreen
import hashlib
import GeoIP

from config import *
from utils import *

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
        self.handlers.update({
                curses.KEY_END: self.h_end,
                curses.KEY_HOME: self.h_home})


    def h_home(self, inp):
        index = self.cursor_position -1 
        while(index > 0):
            if self.value[index] == "\n":
                index += 1
                break
            index -= 1
        self.cursor_position = index

    def h_end(self, inp):
        self.cursor_position = self.value.find('\n', self.cursor_position)
        if self.cursor_position == -1:
            self.cursor_position = len(self.value)

    def h_addch(self, inp):
        if len(self.value) < self.max_length and self.value.count('\n') < self.max_lines:
            return super(MaxMultiLineEdit, self).h_addch(inp)
        return

    def h_delete_right(self, inp):
        super(MaxMultiLineEdit, self).h_delete_right(inp)
        self.reformat_preserve_nl()
        return

    def h_delete_left(self, inp):
        super(MaxMultiLineEdit, self).h_delete_left(inp)
        self.reformat_preserve_nl()
        return

    def reformat_preserve_nl(self, *ignorethese):
        width = self.maximum_display_width
        text  = self.value
        lines = []
        overflow = []
        for former_line in text.split('\n'):
            line = []
            len_line = 0

            if len(overflow) > 0:
                actual_line = ' '.join(overflow) + ' '  + former_line 
                overflow = []
            else:
                actual_line = former_line

            for word in actual_line.split(' '):
                len_word = len(word)
                if len_line + len_word <= width:
                    line.append(word)
                    len_line += len_word + 1
                else:
                    #Once we had an overflow we stay overflowing
                    len_line += width
                    overflow.append(word)

            lines.append(' '.join(line))
            #Overlow pushed into a new line
            if former_line == "" and len(line) > 1:
                lines.append('')

        if len(overflow) > 0:
           lines.append(' '.join(overflow)) 


        self.value = '\n'.join(lines)
        return self.value

class BoxedMaxMultiLineEdit(npyscreen.BoxTitle):
    _contained_widget = MaxMultiLineEdit


class PostForm(npyscreen.ActionPopup):
    CANCEL_BUTTON_BR_OFFSET = (2, 73)
    OK_BUTTON_TEXT = "Post!"
    CANCEL_BUTTON_TEXT = "Cancel"
    DEFAULT_LINES = 33
    DEFAULT_COLUMNS = 80

    def create(self):
        self.value = None
        self.wgTitle = self.add(
            MaxTitleText, name="Title:", max_length=MAX_CHARS_TITLE)
        self.wgName = self.add(MaxTitleText, name="Name:",
                               max_length=MAX_CHARS_NAME)
        self.wgContent = self.add(BoxedMaxMultiLineEdit, name="Post", max_height=23, contained_widget_arguments={
                                  'max_length': MAX_CHARS_POST, 'max_lines': MAX_LINES_POST})
        self.wgFooter = self.add(npyscreen.FixedText)
        self.wgFooter.editable = False

        self.wgFiles = self.add(npyscreen.FormControlCheckbox, name="Enable Files", width= 20)
        self.nextrely -= 1
        self.nextrelx += 20
        self.wgPassword = self.add(MaxTitleText, name="PASSWORD:", max_length=MAX_CHARS_TITLE)
        self.nextrelx -= 20
        self.wgFiles.addVisibleWhenSelected(self.wgPassword)


        self.nextrely += 1
        self.wCancel = self.add(npyscreen.MiniButtonPress,
                                name="Hide", when_pressed_function=self.on_hide)

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

        hashphrase = None
        salt = None

        if self.wgFiles.value:
            salt = os.urandom(32)
            hashphrase = hashlib.pbkdf2_hmac('sha256', self.wgPassword.value.encode("utf-8"), salt, 100000)
 

        threadid = self.parentApp.myDatabase.post(self.parentApp.myBoardId, self.parentApp.myThreadId,
                                       self.wgName.value, self.wgTitle.value, self.wgContent.value, country, hashphrase, salt)

        if SFTP_INTEGRATION:
            thread_path = get_local_path(self.parentApp.myDatabase, self.parentApp.myBoardId, threadid)
            if not os.path.isdir(thread_path):
                os.makedirs(thread_path)

        self.parentApp.switchFormPrevious()

    def on_cancel(self):
        self.parentApp.myThreadTitle = ""
        self.parentApp.myThreadContent = ""
        self.parentApp.switchFormPrevious()

    def on_hide(self):
        if self.parentApp._FORM_VISIT_LIST[-2] == "THREAD":
            self.parentApp.myThreadTitle = self.wgTitle.value
            self.parentApp.myThreadContent = self.wgContent.value
        else:
            self.parentApp.myThreadTitle = ""
            self.parentApp.myThreadContent = ""

        self.parentApp.switchFormPrevious()
