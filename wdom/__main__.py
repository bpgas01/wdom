#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
from pathlib import Path

logger = logging.getLogger('wdom')
_CURFILE = Path(__file__).resolve()
_CURDIR = _CURFILE.parent.resolve()

if __name__ == '__main__':
    sys.path.insert(0, str(_CURDIR.parent.resolve()))


def main():
    from wdom.options import parse_command_line
    parse_command_line()

    # ADD js/css/template files for autoreload
    from tornado import autoreload
    for file_ in (_CURDIR.glob('_static/js/*.js')):
        autoreload.watch(str(file_))
    for file_ in (_CURDIR.glob('_static/css/*.css')):
        autoreload.watch(str(file_))
    for file_ in (_CURDIR.glob('_templates/*.html')):
        autoreload.watch(str(file_))

    # from tornado.ioloop import IOLoop
    from tornado.platform.asyncio import AsyncIOMainLoop
    import asyncio
    AsyncIOMainLoop().install()

    from wdom.server import start_server, get_app
    # from wdom.examples.bootstrap3 import sample_page
    from wdom.examples.markdown_simple import sample_page
    # from wdom.examples.rev_text import sample_page
    # from wdom.examples.data_binding import sample_page
    # from wdom.examples.todo import sample_page
    from wdom.log import configure_logger
    configure_logger()
    page = sample_page()
    app = get_app(document=page)
    server = start_server(app=app)
    loop = asyncio.get_event_loop()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        server.stop()
        loop.close()
        logger.info('Server terminated')
    # IOLoop.current().start()


if __name__ == '__main__':
    main()

