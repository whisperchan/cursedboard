import sys
import os
import curses
import npyscreen


from img2txt import img2txt
from img2txt import ansi
from PIL import Image

def load_and_resize_image(imgname, antialias, columns, rows, aspectRatio = 1.0, fit_height = False):
    img = Image.open(imgname)

    # force image to RGBA - deals with palettized images (e.g. gif) etc.
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # need to change the size of the image?
    # First apply aspect ratio change (if any) - just need to adjust one axis
    # so we'll do the height.

    native_width, native_height = img.size

    new_width = native_width
    new_height = native_height

    new_height = int(float(aspectRatio) * native_height)

    rate = float(rows if fit_height else columns)/(new_height if fit_height else new_width)
    new_width = int(rate * new_width) 
    new_height = int(rate * new_height)

    # Now isotropically resize up or down (preserving aspect ratio)
    if fit_height and new_width > columns:
        rate = float(columns) / new_width
        new_width = int(rate * new_width)  
        new_height = int(rate * new_height)

    if native_width != new_width or native_height != new_height:
        img = img.resize((new_width, new_height), Image.ANTIALIAS if antialias else Image.NEAREST)

    return img

def generate_img(imgname, columns, rows, dither = True, antialiasing = True, fit_height = False):
    bgcolor = None
    target_aspect_ratio = 0.5   # default target_aspect_ratio: 1.0

    try:
        img = load_and_resize_image(imgname, antialiasing, columns, rows, target_aspect_ratio, fit_height)
    except IOError:
        return "File not found: " + imgname

    # Dither _after_ resizing
    if dither:
        img = img2txt.dither_image_to_web_palette(img, bgcolor)

    # get pixels
    pixel = img.load()

    width, height = img.size

    # Since the "current line" was not established by us, it has been
    # filled with the current background color in the
    # terminal. We have no ability to read the current background color
    # so we want to refill the line with either
    # the specified bg color or if none specified, the default bg color.
    if bgcolor is not None:
        # Note that we are making the assumption that the viewing terminal
        # supports BCE (Background Color Erase) otherwise we're going to
        # get the default bg color regardless. If a terminal doesn't
        # support BCE you can output spaces but you'd need to know how many
        # to output (too many and you get linewrap)
        fill_string = ansi.getANSIbgstring_for_ANSIcolor(
            ansi.getANSIcolor_for_rgb(bgcolor))
    else:
        # reset bg to default (if we want to support terminals that can't
        # handle this will need to instead use 0m which clears fg too and
        # then when using this reset prior_fg_color to None too
        fill_string = "\x1b[49m"
    fill_string += "\x1b[K"          # does not move the cursor

    content = fill_string
    content += ansi.generate_ANSI_from_pixels(pixel, width, height, bgcolor)[0]

    # Undo residual color changes, output newline because
    # generate_ANSI_from_pixels does not do so
    # removes all attributes (formatting and colors)
    content +="\x1b[0m\n"

    return content

class ImagePager(npyscreen.DummyWidget):
    def __init__(self, *args, **keywords):
        super(ImagePager, self).__init__(*args, **keywords)
        self.start_display_at = 0
        self.dither = True
        self.antialiasing = True
        self.file = None
        self.fit = True
        self.height = keywords['height']

    def set_file(self, filename):
        self.file = filename
        self.render_image()

    def update(self, clear=True):
        curses.def_prog_mode()
        curses.reset_shell_mode()

        sys.stdout.write('\033[2J')
        sys.stdout.write('\033[H')

        def bool_map(v):
            return "On" if v else "Off"
        sys.stdout.write("[a]ntialiasing: {} [d]ither: {} [f]it horizontal: {}\n".format(bool_map(self.antialiasing), bool_map(self.dither), bool_map(self.fit)))

        for i in range(self.start_display_at, self.start_display_at+min(len(self.values)-self.start_display_at, self.height-2)):
            sys.stdout.write(self.values[i])
            sys.stdout.write("\n")

        curses.reset_prog_mode()

    def set_up_handlers(self):
        super(ImagePager, self).set_up_handlers()
        self.handlers = {
                    curses.KEY_UP:      self.h_scroll_line_up,
                    curses.KEY_LEFT:    self.h_scroll_line_up,
                    curses.KEY_DOWN:    self.h_scroll_line_down,
                    curses.KEY_RIGHT:   self.h_scroll_line_down,
                    'd': self.toggle_dither,
                    'a': self.toggle_antialiasing,
                    'f': self.toggle_fit,
                }

    def h_scroll_line_up(self, input):
        if self.start_display_at == 0:
            return

        self.start_display_at = max(self.start_display_at - 1, 0)
        self.update()
        

    def h_scroll_line_down(self, input):
        if len(self.values) > self.height and self.start_display_at < len(self.values)-self.height-1:
            self.start_display_at += 1
            self.update()

    def render_image(self):
        if not self.file:
            self.values = ['No file']
            return

        self.values = generate_img(self.file, self.width, self.height, self.dither, self.antialiasing, self.fit).split("\n")

    def toggle_dither(self, key):
        self.dither = not self.dither
        self.render_image()
        self.update()

    def toggle_antialiasing(self, key):
        self.antialiasing = not self.antialiasing
        self.render_image()
        self.update()

    def toggle_fit(self, key):
        self.fit = not self.fit
        self.start_display_at = 0
        self.render_image()
        self.update()

class ImageViewer(npyscreen.FormBaseNew):
    MAIN_WIDGET_CLASS = ImagePager
    def __init__(self, *args, **keywords):
        self.draw_form = self._print
        super(ImageViewer, self).__init__(*args, **keywords)

    def create(self):
        self.wImage = self.add(self.__class__.MAIN_WIDGET_CLASS, rely=0, relx=0, height=self.lines, width=self.columns)
        pass

    def beforeEditing(self,):
        self.add_handlers({
            curses.KEY_BACKSPACE: self.parentApp.switchFormPrevious,
        })

        if not os.path.isfile(self.parentApp.myFile):
            self.parentApp.switchFormPrevious()
        self.wImage.set_file(self.parentApp.myFile)
        self.wImage.start_display_at = 0

    def _print(self):
        pass
