import curses
import random
import time
import re
import npyscreen


MOTD = """
=================.,=====================.,=====================.,=====================.,=====================.
|||||||||||||||| || ||||||||||||||||||| || ||||||||||||||||||| || ||||||||||||||||||| || ||||||||||||||||||| |
----------------.||.-------------------.||.-------------------.||.-------------------.||.-------------------.|
MMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM ||
----------------.||.-------------------.||.-------------------.||.-------------------.||.-------------------.|
MMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM ||
----------------.||.-------------------.||.-------------------.||.-------------------.||.-------------------.|
MMMM  O  MMMMMM |||| WHISPE  O  RMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM ||
----------------.||.-------------------.||.-------------------.||.-------------------.||.-------------------.|
MMMM  O  MMMMMM |||| MMMMMM  O   CHAN  |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM ||
----------------.||.-------------------.||.-------------------.||.-------------------.||.-------------------.|
MMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM ||
----------------.||.-------------------.||.-------------------.||.-------------------.||.-------------------.|
MMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM ||
----------------.||.-------------------.||.-------------------.||.-------------------.||.-------------------.|
MMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM ||
----------------.||.-------------------.||.-------------------.||.-------------------.||.-------------------.|
MMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM ||
----------------.||.-------------------.||.-------------------.||.-------------------.||.-------------------.|
MMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM ||
----------------.||.-------------------.||.-------------------.||.-------------------.||.-------------------.|
MMMM  O  :h for |||| help    O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM |||| MMMMMM  O  MMMMMM ||
----------------'||`-------------------'||`-------------------'||`-------------------'||`-------------------'|
=============I===´`=====================´`=====================´`=====================´`=====================´
             |           we're the bits that quietly exchange in the bustling flow around the globe
             |                 2okzlsboulbv6y22foslk7cvgi3nqzj2a7tsofhkzvh6jytjcoxlqlad.onion
~~~~~~~~~~~~~´        NEWS: sftp bit@whisper.onthewifi.com 10MB file size limit, simple ASCII filenames
"""

line_state = 0
flir = 0



class MotdTextfield(npyscreen.Textfield):
    '''Special textfield for animating the motd'''
    def __init__(self, *args, **keywords):
        super(MotdTextfield, self).__init__(*args, **keywords)
        self.syntax_highlighting = True
        random.seed(time.time())

    def update_highlighting(self, start=None, end=None, clear=False):
        global line_state
        global flir
        value = self.display_value(self.value)
        # highlighting color
        normal = self.parent.theme_manager.findPair(self, 'DEFAULT')
        yellow = self.parent.theme_manager.findPair(self, 'WARNING')
        cyan = self.parent.theme_manager.findPair(self, 'STANDOUT')
        green = self.parent.theme_manager.findPair(self, 'SAFE')
        blue = self.parent.theme_manager.findPair(self, 'NO_EDIT')
        red = self.parent.theme_manager.findPair(self, 'DANGER')

        color = [normal]*len(value)


        if line_state < 14:
            if value.find("~~~~~~~~~~~~~´") > -1:
                color[line_state] = blue
                line_state = (line_state + 1) % 18
        elif line_state == 14:
            if value.find("             |                 2") > -1:
                color[13] = blue
                line_state = (line_state + 1) % 18
        elif line_state == 15:
            if value.find("             |           w") > -1:
                color[13] = blue
                line_state = (line_state + 1) % 18
        elif line_state == 16:
            if value.find("=============I") > -1:
                color[13] = blue
                line_state = (line_state + 1) % 18
        elif line_state == 17:
            if value.find("=============I") > -1:
                line_state = (line_state + 1) % 18

        regex = re.compile("NEWS:")
        for group in regex.finditer(value):
            position = group.span()
            for i in range(position[0], position[1]):
                color[i] = random.choice([yellow, cyan, green, red])

        regex = re.compile(":h for")
        for group in regex.finditer(value):
            position = group.span()
            for i in range(position[0], position[1]):
                color[i] = red | curses.A_BOLD

        regex = re.compile("help")
        for group in regex.finditer(value):
            position = group.span()
            for i in range(position[0], position[1]):
                color[i] = red | curses.A_BOLD


        regex = re.compile("O")
        for group in regex.finditer(value):
            position = group.span()
            for i in range(position[0], position[1]):
                if line_state == 17:
                    color[i] = blue
                    continue
                if random.random() > 0.97:
                    color[i] = red
                elif random.random() > 0.95:
                    color[i] = yellow
                else:
                    color[i] = green

        regex = re.compile("WHISPE")
        for group in regex.finditer(value):
            if random.random() > 0.80:
                flir = cyan
            else:
                flir = normal

            position = group.span()
            for i in range(position[0], position[1]):
                color[i] = flir

        regex = re.compile("R")
        for group in regex.finditer(value):
            position = group.span()
            for i in range(position[0], position[1]):
                color[i] = flir

        regex = re.compile("CHAN")
        for group in regex.finditer(value):
            position = group.span()
            for i in range(position[0], position[1]):
                color[i] = flir

        self._highlightingdata = color

class MotdPager(npyscreen.Pager):
    ''' Pager to display MOTD '''
    _contained_widgets = MotdTextfield
