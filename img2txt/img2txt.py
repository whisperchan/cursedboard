import sys
from docopt import docopt
from PIL import Image
import ansi
from .graphics_util import alpha_blend


def HTMLColorToRGB(colorstring):
    """ convert #RRGGBB to an (R, G, B) tuple """
    colorstring = colorstring.strip()
    if colorstring[0] == '#':
        colorstring = colorstring[1:]
    if len(colorstring) != 6:
        raise ValueError(
            "input #{0} is not in #RRGGBB format".format(colorstring))
    r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
    r, g, b = [int(n, 16) for n in (r, g, b)]
    return (r, g, b)


def generate_HTML_for_image(pixels, width, height):

    string = ""
    # first go through the height,  otherwise will rotate
    for h in range(height):
        for w in range(width):

            rgba = pixels[w, h]

            # TODO - could optimize output size by keeping span open until we
            # hit end of line or different color/alpha
            #   Could also output just rgb (not rgba) when fully opaque - if
            #   fully opaque is prevalent in an image
            #   those saved characters would add up
            string += ("<span style=\"color:rgba({0}, {1}, {2}, {3});\">"
                       "▇</span>").format(
                rgba[0], rgba[1], rgba[2], rgba[3] / 255.0)

        string += "\n"

    return string


def generate_grayscale_for_image(pixels, width, height, bgcolor):

    # grayscale
    color = "MNHQ$OC?7>!:-;. "

    string = ""
    # first go through the height,  otherwise will rotate
    for h in range(height):
        for w in range(width):

            rgba = pixels[w, h]

            # If partial transparency and we have a bgcolor, combine with bg
            # color
            if rgba[3] != 255 and bgcolor is not None:
                rgba = alpha_blend(rgba, bgcolor)

            # Throw away any alpha (either because bgcolor was partially
            # transparent or had no bg color)
            # Could make a case to choose character to draw based on alpha but
            # not going to do that now...
            rgb = rgba[:3]

            string += color[int(sum(rgb) / 3.0 / 256.0 * 16)]

        string += "\n"

    return string


def load_and_resize_image(imgname, antialias, maxLen, aspectRatio):

    if aspectRatio is None:
        aspectRatio = 1.0

    img = Image.open(imgname)

    # force image to RGBA - deals with palettized images (e.g. gif) etc.
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # need to change the size of the image?
    if maxLen is not None or aspectRatio != 1.0:

        native_width, native_height = img.size

        new_width = native_width
        new_height = native_height

        # First apply aspect ratio change (if any) - just need to adjust one axis
        # so we'll do the height.
        if aspectRatio != 1.0:
            new_height = int(float(aspectRatio) * new_height)

        # Now isotropically resize up or down (preserving aspect ratio) such that 
        # longer side of image is maxLen 
        if maxLen is not None:
            rate = float(maxLen) / max(new_width, new_height)
            new_width = int(rate * new_width)  
            new_height = int(rate * new_height)

        if native_width != new_width or native_height != new_height:
            img = img.resize((new_width, new_height), Image.ANTIALIAS if antialias else Image.NEAREST)

    return img


def floydsteinberg_dither_to_web_palette(img):

    # Note that alpha channel is thrown away - if you want to keep it you need to deal with it yourself
    #
    # Here's how it works:
    #   1. Convert to RGB if needed - we can't go directly from RGBA because Image.convert will not dither in this case
    #   2. Convert to P(alette) mode - this lets us kick in dithering.
    #   3. Convert back to RGBA, which is where we want to be 
    #
    # Admittedly converting back and forth requires more memory than just dithering directly
    # in RGBA but that's how the library works and it isn't worth writing it ourselves
    # or looking for an alternative given current perf needs.

    if img.mode != 'RGB': 
        img = img.convert('RGB')     
    img = img.convert(mode="P", matrix=None, dither=Image.FLOYDSTEINBERG, palette=Image.WEB, colors=256)
    img = img.convert('RGBA')    
    return img


def dither_image_to_web_palette(img, bgcolor):
    
    if bgcolor is not None:
        # We know the background color so flatten the image and bg color together, thus getting rid of alpha
        # This is important because as discussed below, dithering alpha doesn't work correctly.
        img = Image.alpha_composite(Image.new("RGBA", img.size, bgcolor), img)  # alpha blend onto image filled with bgcolor
        dithered_img = floydsteinberg_dither_to_web_palette(img)    
    else:
     
        """
        It is not possible to correctly dither in the presence of transparency without knowing the background
        that the image will be composed onto. This is because dithering works by propagating error that is introduced 
        when we select _available_ colors that don't match the _desired_ colors. Without knowing the final color value 
        for a pixel, it is not possible to compute the error that must be propagated FROM it. If a pixel is fully or 
        partially transparent, we must know the background to determine the final color value. We can't even record
        the incoming error for the pixel, and then later when/if we know the background compute the full error and 
        propagate that, because that error needs to propagate into the original color selection decisions for the other
        pixels. Those decisions absorb error and are lossy. You can't later apply more error on top of those color
        decisions and necessarily get the same results as applying that error INTO those decisions in the first place.   
        
        So having established that we could only handle transparency correctly at final draw-time, shouldn't we just 
        dither there instead of here? Well, if we don't know the background color here we don't know it there either. 
        So we can either not dither at all if we don't know the bg color, or make some approximation. We've chosen 
        the latter. We'll handle it here to make the drawing code simpler. So what is our approximation? We basically
        just ignore any color changes dithering makes to pixels that have transparency, and prevent any error from being 
        propagated from those pixels. This is done by setting them all to black before dithering (using an exact-match 
        color in Floyd Steinberg dithering with a web-safe-palette will never cause a pixel to receive enough inbound error
        to change color and thus will not propagate error), and then afterwards we set them back to their original values. 
        This means that transparent pixels are essentially not dithered - they ignore (and absorb) inbound error but they
        keep their original colors. We could alternately play games with the alpha channel to try to propagate the error 
        values for transparent pixels through to when we do final drawing but it only works in certain cases and just isn't 
        worth the effort (which involves writing the dithering code ourselves for one thing).
        """
        
        # Force image to RGBA if it isn't already - simplifies the rest of the code    
        if img.mode != 'RGBA': 
            img = img.convert('RGBA')    

        rgb_img = img.convert('RGB')    
    
        orig_pixels = img.load()
        rgb_pixels = rgb_img.load()
        width, height = img.size

        for h in range(height):    # set transparent pixels to black
            for w in range(width):
                if (orig_pixels[w, h])[3] != 255:    
                    rgb_pixels[w, h] = (0, 0, 0)   # bashing in a new value changes it!

        dithered_img = floydsteinberg_dither_to_web_palette(rgb_img)    

        dithered_pixels = dithered_img.load() # must do it again
        
        for h in range(height):    # restore original RGBA for transparent pixels
            for w in range(width):
                if (orig_pixels[w, h])[3] != 255:    
                    dithered_pixels[w, h] = orig_pixels[w, h]   # bashing in a new value changes it!

    return dithered_img
