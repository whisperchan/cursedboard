import curses
import re
import textwrap
import os
import glob
import random

from datetime import datetime
import subprocess

import npyscreen

from config import *


def directory_stats(path):
    files = 0
    directories = 0
    for _, dirnames, filenames in os.walk(path):
        files += len(filenames)
        directories += len(dirnames)
    return files, directories

def is_in_sftp(path):
    return path[:len(SFTP_ROOT_DIR)] == SFTP_ROOT_DIR

def get_local_path(database, boardid, threadid):
    return os.path.join(SFTP_ROOT_DIR, database.get_board(boardid)[0], str(threadid))

def get_remote_path(database, boardid, threadid):
    return os.path.join("/", database.get_board(boardid)[0], str(threadid))

def option_binary(args):
    if (args in ['on', '1', 'On']):
        return 1
    if (args in ['off', '0', 'Off']):
        return 0

    return None


def blockify(text, width, count):
    lines = textwrap.wrap(text, width)
    return lines[:count]


def padr(string, size):
    return str(string) + " " * (size - len(str(string)))


def padl(string, size):
    return " " * (size - len(str(string))) + str(string)


def get_connected_users():
    p = subprocess.Popen(["w", UNIX_USER, "-s"], stdout=subprocess.PIPE)
    out = p.communicate()[0]
    if out is None:
        return 0

    return len(out.decode().split("\n")) - 3


def prettydate(created):
    if created == "":
        return "Never"

    now = datetime.now()
    posted = datetime.strptime(created, "%Y-%m-%d %H:%M:%S")
    diff = now - posted

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
        color += [normal] * 2
        color += [yellow] * 4
        color += [yellow | curses.A_BOLD] * MAX_POSTID_LENGTH
        color += [normal] * 2
        color += [normal | curses.A_BOLD] * MAX_CHARS_TITLE
        color += [normal] * 2
        color += [cyan] * MAX_CHARS_NAME
        color += [normal] * 22
        color += [red] * 80
    elif value[:10] == "│ Attached":
        color = [normal, normal]
        color += [yellow]*9
        color += [normal | curses.A_BOLD]*(len(value)-11)

    else:
        if value[:3] == "│ >":
            color = [normal] * 2 + [green] * (len(value) - 2)
        elif value[0] == ">":
            color = [green] * (len(value))
        else:
            color = [normal] * len(value)

        # bold
        p = re.compile("\*[a-zA-Z0-9!+-.,=': ]+\*")
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
    DEFAULT_COLUMNS = 70
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


def cursed_notify(message, title="Message", form_color='STANDOUT', editw=0,):
    F = PopupBig(name=title, color=form_color, wide=True)
    F.preserve_selected_widget = True
    mlw = F.add(PagerHighlight,)
    mlw_width = mlw.width - 1
    mlw.values = _wrap_message_lines(message, mlw_width)
    F.editw = editw
    F.edit()


