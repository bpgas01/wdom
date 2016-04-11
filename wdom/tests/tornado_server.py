#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from os.path import dirname, abspath
import asyncio

root = dirname(dirname(dirname(abspath(__file__))))
sys.path.append(root)

from wdom.misc import install_asyncio
from wdom import options
from wdom.log import configure_logger
from wdom.document import get_document
from wdom.server_tornado import start_server, stop_server, get_app

install_asyncio()
options.parse_command_line()
configure_logger()
loop = asyncio.get_event_loop()
app = get_app(get_document())
server = start_server(app, loop=loop)
try:
    loop.run_forever()
except Exception:
    stop_server(server)
    loop.stop()
