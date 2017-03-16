#!/usr/bin/env python3
import importlib

import cherrypy
import logging
import os

import sys
from atsrv.attestation_service import JWSProducer
from atsrv.srv import AttestationService
from oic.utils.keyio import build_keyjar

logger = logging.getLogger("")
LOGFILE_NAME = 'farp.log'
hdlr = logging.FileHandler(LOGFILE_NAME)
base_formatter = logging.Formatter(
    "%(asctime)s %(name)s:%(levelname)s %(message)s")

hdlr.setFormatter(base_formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', dest='port', default=80, type=int)
    parser.add_argument('-t', dest='tls', action='store_true')
    parser.add_argument('-f', dest='fdir', required=True)
    parser.add_argument(dest="config")
    args = parser.parse_args()

    folder = os.path.abspath(os.curdir)
    sys.path.insert(0, ".")
    conf = importlib.import_module(args.config)

    if args.port:
        _host = "{}:{}".format(conf.HOST, args.port)
    else:
        _host = conf.HOST

    cherrypy.config.update(
        {'environment': 'production',
         'log.error_file': 'site.log',
         'tools.trailing_slash.on': False,
         'server.socket_host': '0.0.0.0',
         'log.screen': True,
         'tools.sessions.on': True,
         'tools.encode.on': True,
         'tools.encode.encoding': 'utf-8',
         'server.socket_port': args.port
         })

    provider_config = {
        '/': {
            'root_path': 'localhost',
            'log.screen': True
        },
        '/static': {
            'tools.staticdir.dir': os.path.join(folder, 'static'),
            'tools.staticdir.debug': True,
            'tools.staticdir.on': True,
            'log.screen': True,
            'cors.expose_public.on': True
        }}

    _kj = build_keyjar(conf.KEY_DEF)[1]
    value_conv = JWSProducer(_host, sign_keys=_kj, sign_alg="RS256")

    cherrypy.tree.mount(AttestationService(args.fdir, value_conv), '/',
                        provider_config)

    # If HTTPS
    if args.tls:
        cherrypy.server.ssl_certificate = conf.SERVER_CERT
        cherrypy.server.ssl_private_key = conf.SERVER_KEY
        if conf.CA_BUNDLE:
            cherrypy.server.ssl_certificate_chain = conf.CA_BUNDLE

    cherrypy.engine.start()
    cherrypy.engine.block()
