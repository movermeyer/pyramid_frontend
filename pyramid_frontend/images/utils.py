from __future__ import absolute_import, print_function, division

import math
from cStringIO import StringIO

from PIL import Image, ImageColor, ImageChops


def check(image_file):
    """
    Given a file object, check to see if the contents is a valid image. If so,
    return the file format. Otherwise, raise exceptions.
    """
    im = Image.open(image_file)
    # Raises exceptions if the file is broken in any way.
    im.verify()
    return (im.format, im.mode)


def possible_extensions(format):
    """
    For a given format (as returned by PIL) return a list of possible file
    extensions that can be used with this format. The first extension in the
    returned list is the preferred one.
    """
    return {'BMP': ['bmp'],
            'GIF': ['gif'],
            'JPEG': ['jpg', 'jpe', 'jpeg'],
            'PPM': ['ppm', 'pbm'],
            'PCX': ['pcx'],
            'PNG': ['png'],
            'PSD': ['psd'],
            'TGA': ['tga'],
            'TIFF': ['tif', 'tiff']}[format]


def flatten_alpha(im, background='white'):
    "Composite an RGBA image with a flat background."
    if im.mode == "RGBA":
        ni = Image.new("RGB", im.size, background)
        ni.paste(im, im)
        im = ni
    return im


def flatten_paletted(im, background=255):
    if 'transparency' in im.info:
        try:
            background_int = int(background)
        except ValueError:
            background_int = ImageColor.getcolor(background, 'L')
        transparency = im.info['transparency']
        x = transparency * 3
        p = im.getpalette()
        for x in range(x, x + 3):
            p[x] = background_int
        im.putpalette(p)
    return im


def pad_image(im, dimensions, mode=None, color=None):
    """
    Pad an image to a given set of dimensions.
    """
    w, h = im.size
    desired_w, desired_h = (max(a, b) for a, b in zip(im.size, dimensions))
    new = Image.new(mode or 'RGB', (desired_w, desired_h), color or 'white')
    woff = int((desired_w - w) / 2)
    hoff = int((desired_h - h) / 2)
    new.paste(im, (woff, hoff))
    return new


def crop_to_ratio(im, ar):
    """
    Crop an image to a given aspect ratio.  Rounds dimensions up.
    """
    im_ar = float(im.size[0]) / im.size[1]
    w, h = (im.size[1] * ar, im.size[1]) if im_ar > ar else \
           (im.size[0], im.size[0] / ar)
    return im.crop((0, 0, int(math.ceil(w)), int(math.ceil(h))))


def image_entropy(im):
    hist = im.histogram()
    hist_size = sum(hist)
    # normalize
    hist = [float(h) / hist_size for h in hist]
    return -sum([p * math.log(p, 2) for p in hist if p != 0])


def crop_entropy_width(im, desired_w):
    w, h = im.size
    while w > desired_w:
        # Remove slice from left or right side, whichever has less entropy.
        slice_width = min(w - desired_w, int(math.floor(w * 0.1)))
        left = im.crop((0, 0, slice_width, h))
        right = im.crop((w - slice_width, 0, w, h))

        if image_entropy(left) < image_entropy(right):
            # Crop off left side.
            im = im.crop((slice_width, 0, w, h))
        else:
            # Crop off right side.
            im = im.crop((0, 0, w - slice_width, h))

        w, h = im.size

    return im


def crop_entropy_height(im, desired_h):
    w, h = im.size
    while h > desired_h:
        # Remove slice from top or bottom, whichever has less entropy.
        slice_height = min(h - desired_h, int(math.floor(h * 0.1)))
        top = im.crop((0, 0, w, slice_height))
        bottom = im.crop((0, h - slice_height, w, h))

        if image_entropy(bottom) < image_entropy(top):
            im = im.crop((0, 0, w, h - slice_height))
        else:
            im = im.crop((0, slice_height, w, h))

        w, h = im.size

    return im


def crop_entropy(im, dimensions):
    """
    Scale and crop the image to the desired aspect ratio by slicing off a bit
    at a time.  Slice off the edge which is lowest entropy.
    """
    # First resize this so that the longer dimension matches the desired
    # dimension.
    input_w, input_h = im.size
    desired_w, desired_h = dimensions

    input_ar = float(input_w) / float(input_h)
    desired_ar = float(desired_w) / float(desired_h)

    if input_ar > desired_ar:
        scale_h = desired_h
        scale_w = int(input_h * input_ar) + 1
        im.thumbnail((scale_w, scale_h), Image.ANTIALIAS)
        return crop_entropy_width(im, desired_w)
    elif input_ar < desired_ar:
        scale_w = desired_w
        scale_h = int(input_w / input_ar) + 1
        im.thumbnail((scale_w, scale_h), Image.ANTIALIAS)
        return crop_entropy_height(im, desired_h)
    else:
        # AR already matches exactly, no need to crop.
        im.thumbnail((desired_w, desired_h), Image.ANTIALIAS)
        return im


def placeholder(im, size=(1, 1)):
    """
    Return a StringIO buffer to act as a placeholder for the given ImageMeta.
    If ImageMeta stored dimensions, this function would use them.
    """
    i = Image.new('RGB', size, 'white')
    buf = StringIO()
    i.save(buf, {
        "jpg": "JPEG",
        "tiff": "TIFF",
        "tif": "TIFF",
    }.get(im.original_ext.lower(), im.original_ext))
    buf.seek(0)
    return buf


def colors_differ(a, b, tolerance):
    manhattan_distance = sum([abs(i - j) for i, j in zip(a, b)])
    return manhattan_distance > tolerance


def is_white_background(im, tolerance=180):
    """
    Check if this image is against a white background: that is, if every border
    pixel is white.
    """
    w, h = im.size
    im = im.convert('RGB')
    array = im.load()
    white = (255, 255, 255)
    for x in range(w):
        # Top border
        if colors_differ(array[x, 0], white, tolerance):
            return False
        # Bottom border
        if colors_differ(array[x, h - 1], white, tolerance):
            return False
    for y in range(h):
        # Left border
        if colors_differ(array[0, y], white, tolerance):
            return False
        # Right border
        if colors_differ(array[w - 1, y], white, tolerance):
            return False
    return True


def is_larger(im, dimensions):
    """
    Check if this image is currently larger in either axis than the desired
    dimensions.
    """
    w, h = im.size
    desired_w, desired_h = dimensions
    return (w > desired_w) or (h > desired_h)


def bounding_box(im, tolerance=0):
    """
    A bounding box algorithm that has some tolerance for fuzziness.
    """
    bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -tolerance)
    return diff.getbbox()
