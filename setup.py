from __future__ import print_function

import os
from setuptools import setup
from distutils.command.build import build as _build


executables = [
    'jpegoptim',
    'pngcrush',
    'optipng',
    'convert',  # From GraphicsMagick or ImageMagick.
    'lessc',
    'r.js',
]


def which(exe):
    for path in os.environ['PATH'].split(os.pathsep):
        fpath = os.path.join(path, exe)
        if os.path.exists(fpath) and os.access(fpath, os.X_OK):
            return fpath


class build(_build):
    def finalize_options(self):
        _build.finalize_options(self)
        for exe in executables:
            print('checking for %r...' % exe)
            fpath = which(exe)
            if not fpath:
                print('WARNING: Missing %r executable!' % exe)
            else:
                print(fpath)


setup(name='pyramid_frontend',
      cmdclass={'build': build},
      version='0.1',
      description='Themes, image filtering, and frontend asset handling.',
      long_description='',
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Framework :: Pyramid',
      ],
      keywords='pyramid themes frontend assets',
      url='http://github.com/cartlogic/pyramid_frontend',
      author='Scott Torborg',
      author_email='scott@cartlogic.com',
      install_requires=[
          'Pyramid>=1.4.5',
          'Pillow>=2.1.0',      # Provides PIL
          'Mako>=0.9.0',
          # These are for tests.
          'coverage',
          'nose>=1.1',
          'nose-cover3',
      ],
      license='MIT',
      packages=['pyramid_frontend'],
      test_suite='nose.collector',
      tests_require=['nose'],
      include_package_data=True,
      zip_safe=False,
      entry_points="""\
      [console_scripts]
      pcompile = pyramid_frontend.compile:main
      """)
