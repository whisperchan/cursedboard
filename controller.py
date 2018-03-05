import npyscreen 
from utils import *
from config import *

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
            'auth': self.auth,
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
        if not country_balls:
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
        if self.parent.parentApp._THISFORM.FORM_NAME != "BOARD":
            self.parent.wStatus2.value = "Not on a board"
            return

        self.parent.parentApp.switchForm("POST")

    def reply(self, *args):
        # can be made context aware
        if self.parent.parentApp._THISFORM.FORM_NAME != "THREAD":
            self.parent.wStatus2.value = "Not in a thread"
            return

        self.parent.parentApp.switchForm("POST")

    def help(self, *args):
        cursed_notify(HELP_TEXT, title="Help")

    def rules(self, *args):
        placard = RULES_TEXT
        cursed_notify(placard, title="House Rules")
