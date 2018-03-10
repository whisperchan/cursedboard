import sys

from img2txt import img2txt
from img2txt import ansi

def generate_img(imgname, maxLen):
    antialias = True
    dither = True
    target_aspect_ratio = .5   # default target_aspect_ratio: 1.0


    try:
        # add fully opaque alpha value (255)
        bgcolor = HTMLColorToRGB(bgcolor) + (255, )
    except:
        bgcolor = None


    try:
        img = img2txt.load_and_resize_image(imgname, antialias, maxLen, target_aspect_ratio)
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

    def update(self, clear=True):
        print('\033[H')
        curses.def_prog_mode()
        curses.reset_shell_mode()

        
        for i in range(self.start_display_at, self.start_display_at+min(len(self.values)-self.start_display_at, self.height)):
            sys.stdout.write(self.values[i])
            sys.stdout.write("\n")

        curses.reset_prog_mode()

    def set_up_handlers(self):
        super(ImgPager, self).set_up_handlers()
        self.handlers = {
                    curses.KEY_UP:      self.h_scroll_line_up,
                    curses.KEY_LEFT:    self.h_scroll_line_up,
                    curses.KEY_DOWN:    self.h_scroll_line_down,
                    curses.KEY_RIGHT:   self.h_scroll_line_down,
                }

    def h_scroll_line_up(self, input):
        self.start_display_at = max(self.start_display_at - 1, 0)
        self.update()
        

    def h_scroll_line_down(self, input):
        if len(self.values) > self.height and self.start_display_at < len(self.values)-self.height-1:
            self.start_display_at += 1
            self.update()


class ImageViewer(npyscreen.FormBaseNew):
    MAIN_WIDGET_CLASS = ImagePager
    def __init__(self, *args, **keywords):
        self.draw_form = self._print
        super(ImageViewer, self).__init__(*args, **keywords)

    def create(self):
        self.wImage = self.add(self.__class__.MAIN_WIDGET_CLASS, rely=0, relx=0, height=self.lines, width=self.columns )
        pass

    def beforeEditing(self,):
        self.add_handlers({
            curses.KEY_BACKSPACE: self.parentApp.switchFormPrevious,
        })

        if not os.path.isfile(self.parentApp.myFile):
            self.parentApp.switchFormPrevious()

        self.wImage.start_display_at = 0
        self.wImage.values = generate_img(self.parentApp.myFile, self.columns).split("\n")
        return


    def _print(self):
        pass
