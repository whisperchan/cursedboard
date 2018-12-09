import npyscreen 
import session
from utils import *
from config import *

HELP_TEXT = """Navigate with arrow keys, j, k and <tab>. Confirm with enter or space. Go back up with backspace.
These vim style commands can be issued with : as prefix:

h, help      - This message
rules        - Show info
about
info

p, post      - Open the post form on a board/thread optionally with id to reply to
b, board     - Go back to a board from thread
j, jump      - Toggle "Jump to Bottom" for reading threads
l, list      - Go back to overview
f, files     - Opens the file browser context aware
s, session   - Show sessions settings, can be used with RemoteCommand and RequestTTY set to force to automatically rice your experience 
q, quit      - Jack out


auth         - Play god 
admin
       create     - Create a board
       delete     - Delete a post
       nuke       - Nuke a board
       deauth     - Return to the lesser beings


*How to post files to threads:*

For each post a corresponding directory on the sftp server is created. Files in the directory starting with 'postid_' are automatically associated with the matching post if enabled in the post form.If nessecary files can be deleted via the file browser by selecting the file, pressing DEL and supplying the password that was set with the post. They can not be deleted via sftp.

The file browser is context aware, meaning backspace will open the view the browser was called in.

The sftp server allows files up to 10MB and with the filename set 0-9a-Z_-.

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

class ActionController(npyscreen.ActionControllerSimple):
    def create(self):
        self.add_action('^:.*', self.execute_command, False)

        self.CMD = {
            'files': self.files,
            'f': self.files,
            'p': self.post,
            'post': self.post,
            'r': self.post,
            'reply': self.post,
            'b': self.current_board,
            'board': self.current_board,
            'l': self.list,
            'list': self.list,
            'j': self.toggle_jump_to_bottom,
            'jump': self.toggle_jump_to_bottom,
            's': self.show_session,
            'session': self.show_session,
            'q': self.quit,
            'quit': self.quit,
            'admin': self.admin,
            'h': self.help,
            'help': self.help,
            'rules': self.rules,
            'info': self.rules,
            'about': self.rules,
            'auth': self.auth,
            'deauth': self.deauth,
        }

        self.ADMIN = {
            'create': self.create_board,
            'delete': self.delete_post,
            'nuke': self.nuke_board,
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
        if self.parent.parentApp._THISFORM.FORM_NAME != "THREAD":
            self.parent.wStatus2.value = "Not in a thread"
            return

        self.parent.parentApp.myThreadId = 0
        self.parent.parentApp.switchForm("BOARD")

    def list(self, *args):
        self.parent.parentApp.myThreadId = 0
        self.parent.parentApp.myBoardId = 0
        self.parent.parentApp.switchForm("MAIN")

    def auth(self, *args):
        if args is None or len(args) < 2:
            self.parent.wStatus2.value = "auth <password>"
            return

        self.parent.parentApp.authenticate(args[1])

        if self.parent.parentApp.authenticated():
            self.parent.wStatus2.value = "God Mode enabled"
        else:
            self.parent.wStatus2.value = "Denied"

    def deauth(self, *args):
        if self.parent.parentApp.authenticated():
            self.parent.parentApp.deauthenticate()
            self.parent.wStatus2.value = "God Mode disabled"

    def create_board(self, *args):
        if args is None or len(args) < 3:
            self.parent.wStatus2.value = "admin create <name> <countryballs> <description>"
            return

        name = args[0]
        exists = self.parent.parentApp.myDatabase.name_to_bid(name)
        if exists:
            self.parent.wStatus2.value = "Board already exists: %s" %(name,)
            return

        country_balls = option_binary(args[1])
        if country_balls == None:
            self.parent.wStatus2.value = "Countryball Value: Off off 0 On on 1"
            return

        description = " ".join(args[2:])
        self.parent.parentApp.myDatabase.create_board(
            name, description, country_balls)
        self.parent.parentApp.switchForm('MAIN')

    def delete_post(self, *args):
        if args is None or len(args) < 1:
            self.parent.wStatus2.value = "admin delete <postid>"
            return

        if self.parent.parentApp._THISFORM.FORM_NAME != "THREAD":
            self.parent.wStatus2.value = "Not in a thread"
            return

        self.parent.parentApp.myDatabase.delete_post(
            self.parent.parentApp.myBoardId, args[0])
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

        if len(args) > 1 and  re.match("^[0-9]+$",args[1]):
            self.parent.parentApp.reply_to = int(args[1])
        else:
            self.parent.parentApp.reply_to = None

        if self.parent.parentApp._THISFORM.FORM_NAME == "BOARD":
            self.parent.parentApp.switchForm("POST")
            return

        if self.parent.parentApp._THISFORM.FORM_NAME == "THREAD":
            self.parent.parentApp.switchForm("POST")
            return

        self.parent.wStatus2.value = "Not in a thread/board"

    def help(self, *args):
        cursed_notify(HELP_TEXT, title="Help")

    def rules(self, *args):
        cursed_notify(RULES_TEXT, title="House Rules")

    def files(self, *args):
        if not SFTP_INTEGRATION:
            self.parent.wStatus2.value = "Files are not enabled"
            return

        path = SFTP_ROOT_DIR
        if self.parent.parentApp.myBoardId != 0:
            path = os.path.join(path, self.parent.parentApp.myDatabase.get_board(self.parent.parentApp.myBoardId)[0])
            if self.parent.parentApp.myThreadId != 0:
                path = os.path.join(path, str(self.parent.parentApp.myThreadId))
        self.parent.parentApp.myPath = path
        self.parent.parentApp.getForm("FILES").reset_cursor()
        self.parent.parentApp.switchForm("FILES")

    def thread_files(self, *args):
        if not SFTP_INTEGRATION:
            self.parent.wStatus2.value = "Files are not enabled"
            return

        if self.parent.parentApp._THISFORM.FORM_NAME != "THREAD":
            self.parent.wStatus2.value = "Not in a thread"
            return

        placard = "sftp {}:{}".format(HOSTNAME, get_remote_path(self.parent.parentApp.myDatabase, self.parent.parentApp.myBoardId, self.parent.parentApp.myThreadId))
        cursed_notify(placard, title="Upload to Thread")

    def toggle_jump_to_bottom(self, *args):
        session.jump_to_bottom = not session.jump_to_bottom
        self.parent.wStatus2.value = "Jump to bottom: "+str(session.jump_to_bottom)
        if self.parent.parentApp._THISFORM.FORM_NAME == "THREAD" and session.jump_to_bottom:
            self.parent.parentApp.getForm("THREAD").jump_to_bottom()

    def show_session(self, *args):
        cursed_notify(session.to_string(), title="Session Cookie")

