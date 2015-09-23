from __future__ import absolute_import, print_function, division

import shutil
import tempfile
import subprocess
import math
from six import BytesIO
from six.moves import xrange

from PIL import Image

from .utils import (pad_image, flatten_alpha, crop_entropy,
                    is_white_background, is_larger, bounding_box, sharpen)


class Filter(object):
    """
    Filter stage superclass. Instances are called with some input data and
    produce some output data. Has some useful methods for processing.

    Filter instances are called on input data and return output data. Filters
    can take an arbitrary input and output, but by convention will tend to pass
    either PIL images or file-like objects.
    """

    def adapt_input(self, input):
        """
        Given a PIL image or a file-like object, return the PIL image.
        """
        if hasattr(input, 'getpixel'):
            im = input
            assert im.mode != 'CMYK', \
                "CMYK-mode Image instance can't be passed directly to filter"
        else:
            input.seek(0)
            im = Image.open(input).convert('RGBA')
            # Handle CMYK images
            if im.mode == 'CMYK':
                pos = input.tell()
                input.seek(0)
                rgb_input = CMYKFilter()(input)
                input.seek(pos)
                im = Image.open(rgb_input)

        return im

    def __call__(self, input):
        return self.filter(self.adapt_input(input))

    def shell_process(self, input, args, inplace=False):
        """
        Process an image file (on the filesystem) using a shell command.
        """
        input.seek(0)
        temp = tempfile.NamedTemporaryFile()
        shutil.copyfileobj(input, temp)
        temp.flush()
        null = open('/dev/null', 'wb')

        if inplace:
            out = temp
        else:
            out = tempfile.NamedTemporaryFile()

        processed_args = []
        for arg in args:
            if arg == 'IN':
                arg = temp.name
            elif arg == 'OUT':
                arg = out.name
            processed_args.append(arg)

        subprocess.check_call(processed_args,
                              stdout=null,
                              stderr=null,
                              close_fds=True)
        out.seek(0)
        return out


class ThumbFilter(Filter):
    """
    A filter that resizes to a given size, using various mechanisms for
    changing size.
    """
    def __init__(self, dimensions, pad=False, crop=False,
                 crop_whitespace=False, background='white', enlarge=False):

        self.dimensions = dimensions
        self.pad = pad
        self.crop = crop
        self.crop_whitespace = crop_whitespace
        self.background = background
        self.enlarge = enlarge

    def filter(self, im):
        def _pad_dim(src, dst, flag):
            assert isinstance(flag, bool)
            return (dst if flag else src)

        #im = flatten_alpha(im, self.background)

        if self.crop is True:
            should_entropy_crop = True
        elif self.crop == 'nonwhite':
            should_entropy_crop = not is_white_background(im)
        else:
            should_entropy_crop = False

        # FIXME The cropping behavior is not really correct here for dimensions
        # that are partially unspecified.
        if should_entropy_crop and is_larger(im, self.dimensions):
            im = crop_entropy(im, self.dimensions)

        if self.crop_whitespace and is_larger(im, self.dimensions):
            im = im.crop(bounding_box(im))

        # FIXME The enlarge flag should only have any effect if the image
        # actually needs to be enlarged.
        if self.enlarge:
            factor = max(float(self.dimensions[0]) / im.size[0],
                         float(self.dimensions[1]) / im.size[1])
            im = im.resize((int(math.ceil(im.size[0] * factor)),
                            int(math.ceil(im.size[1] * factor))),
                           Image.BICUBIC)

        w, h = im.size
        aspect = float(w) / float(h)
        desired_w, desired_h = self.dimensions
        if (not desired_w) and (not desired_h):
            desired_w, desired_h = w, h
        elif not desired_w:
            desired_w = aspect * desired_h
        elif not desired_h:
            desired_h = desired_w / aspect

        im.thumbnail((desired_w, desired_h), Image.ANTIALIAS)
        if self.pad:
            w = _pad_dim(im.size[0], self.dimensions[0], self.pad)
            h = _pad_dim(im.size[1], self.dimensions[1], self.pad)
            im = pad_image(im, (w, h))
        return im


class VignetteFilter(Filter):
    """
    A filter which vignettes corners a bit, to make a white background image
    stand out a bit against a white page background.
    """
    def __init__(self, falloff=4, extent=40):
        self.falloff = falloff
        self.extent = extent

    def filter(self, im):
        falloff = self.falloff
        extent = self.extent

        def length(start, end):
            start_x, start_y = start
            end_x, end_y = end
            dist_x = end_x - start_x
            dist_y = end_y - start_y
            return math.sqrt((dist_x ** 2) + (dist_y ** 2))

        def light_falloff(radius, outside):
            return ((radius / outside) ** falloff) * extent

        im = im.convert('RGBA')

        w, h = im.size
        center = w / 2, h / 2
        outside = length(center, (0, 0))

        data = []
        for y in xrange(h):
            for x in xrange(w):
                radius = length(center, (x, y))
                factor = light_falloff(radius, outside)
                data.append(factor)

        alpha_im = Image.new('L', im.size)
        alpha_im.putdata(data)
        overlay_im = Image.new('L', im.size, 'black')
        return Image.composite(overlay_im, im, alpha_im)


class CMYKFilter(Filter):
    """
    Convert a file-like object to RGB colorspace using ImageMagick. This should
    be quite robust to weird things like CMYK TIFFs.
    """

    def __call__(self, input):
        return self.shell_process(input, ['convert', 'IN',
                                          '-colorspace', 'rgb',
                                          'OUT'])


class JPGSaver(Filter):
    """
    A JPG saver. Accepts keyword arguments, which will be passed to PIL's
    ``save()`` method. Calls jpegoptim on output.
    """
    def __init__(self, sharpness=None, **kwargs):
        self.sharpness = sharpness
        self.kwargs = kwargs

    def filter(self, im):
        if self.sharpness:
            im = sharpen(im, self.sharpness)
        icc_profile = im.info.get("icc_profile")
        if im.mode.endswith("A"):
            ni = Image.new("RGB", im.size, 'white')
            ni.paste(im, im)
            im = ni
        elif im.mode != "RGB":
            im = im.convert('RGB')
        buf = BytesIO()
        im.save(buf, 'JPEG', icc_profile=icc_profile, **self.kwargs)
        buf.seek(0)
        return buf


class JPGProcessor(Filter):
    """
    Postprocess a JPEG. For now, just uses jpegoptim to do some additional
    lossless slimming.
    """
    def __call__(self, input):
        return self.shell_process(input,
                                  ['jpegoptim', '--strip-all', 'IN'],
                                  inplace=True)


class PNGSaver(Filter):
    """
    Save a file as a 24-bit PNG and return the file-like object
    with PNG data.
    """
    def __init__(self, palette=False, colors=256, sharpness=None,
                 background='white'):
        self.palette = palette
        self.colors = colors
        self.background = background
        self.sharpness = sharpness

    def filter(self, im):
        if self.sharpness:
            im = sharpen(im, self.sharpness)
        buf = BytesIO()
        icc_profile = im.info.get("icc_profile")
        if self.palette:
            if im.mode in ('RGBA', 'LA'):
                alpha = im.split()[3]
                alpha = Image.eval(alpha, lambda a: 255 if a > 0 else 0)
                mask = Image.eval(alpha, lambda a: 255 if a == 0 else 0)

                matte = Image.new("RGBA", im.size, self.background)
                matte.paste(im, (0, 0), im)
                matte = matte.convert("RGB").convert(
                    'P', palette=Image.ADAPTIVE, colors=self.colors - 1)
                matte.paste(self.colors, mask)
                matte.save(buf, "PNG", transparency=self.colors)
            elif im.mode not in ('P'):
                im = im.convert('P', palette=Image.ADAPTIVE,
                                colors=self.colors)
                im.save(buf, 'PNG', icc_profile=icc_profile)
            else:
                im.save(buf, 'PNG', icc_profile=icc_profile)
        else:
            if not im.mode.startswith("RGB"):
                im = im.convert('RGB')
            im.save(buf, 'PNG', icc_profile=icc_profile)
        buf.seek(0)
        return buf


class PNGProcessor(Filter):
    """
    Postprocess a PNG. For now, just uses pngcrush and optipng to do some
    additional lossless slimming.
    """

    def __call__(self, input):
        input = self.shell_process(input, ['pngcrush', 'IN', 'OUT'])
        return self.shell_process(input, ['optipng', 'IN'], inplace=True)
