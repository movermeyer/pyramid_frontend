import os
import os.path
import glob
import pkg_resources
import shutil

from pyramid.config import Configurator

from pyramid_frontend.tests.example import base, foo, bar
from pyramid_frontend.images.files import save_image


samples_dir = pkg_resources.resource_filename('pyramid_frontend.tests', 'data')


def noop_view(request):
    return {}


def bad_return_view(request):
    return 'not-a-dict'


def bad_template_view(request):
    return {}


def image_url_view(request):
    load_images(request)
    return request.image_url('smiley-jpeg-rgb', 'jpg', 'thumb')


def load_images(request):
    """
    Load images from test 'samples' directory to originals dir.
    """
    settings = request.registry.settings
    if settings.get('images-loaded'):
        return
    settings['images-loaded'] = True

    originals = settings['pyramid_frontend.original_image_dir']
    processed = settings['pyramid_frontend.processed_image_dir']
    if os.path.exists(originals):
        shutil.rmtree(originals)
    if os.path.exists(processed):
        shutil.rmtree(processed)
    os.makedirs(originals)
    os.makedirs(processed)

    for filename in glob.glob(os.path.join(samples_dir, '*.*')):
        f = open(filename, 'rb')
        name, original_ext = os.path.basename(filename).rsplit('.', 1)
        save_image(settings, name, original_ext, f)


def make_app():
    settings = {
        'pyramid_frontend.theme': 'foo',
        'pyramid_frontend.original_image_dir': '/tmp/pfe-image-originals',
        'pyramid_frontend.processed_image_dir': '/tmp/pfe-image-processed',
    }
    config = Configurator(settings=settings)

    config.include('pyramid_frontend')

    config.add_image_filter('thumb', width=200, height=200, crop=True)

    config.add_theme(base.BaseTheme)
    config.add_theme(foo.FooTheme)
    config.add_theme(bar.BarTheme)

    config.add_route('index', '/')
    config.add_route('article', '/article')
    config.add_route('bad-return', '/bad-return')
    config.add_route('bad-template', '/bad-template')
    config.add_route('image-url', '/image-url')

    config.add_view(noop_view, route_name='index', renderer='index.html')
    config.add_view(noop_view, route_name='article', renderer='article.html')
    config.add_view(bad_return_view, route_name='bad-return',
                    renderer='index.html')
    config.add_view(bad_template_view, route_name='bad-template',
                    renderer='bad.html')
    config.add_view(image_url_view, route_name='image-url', renderer='string')

    return config.make_wsgi_app()


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    app = make_app()
    server = make_server('0.0.0.0', 8080, app)
    server.serve_forever()