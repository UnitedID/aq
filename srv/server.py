#!/usr/bin/env python3
import cherrypy
import logging
import os

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


SERVER_KEY = 'certs/key.pem'
SERVER_CERT = 'certs/cert.pem'
CA_BUNDLE = None
HOST = 'http://localhost'
KEY_DEF = [{"type": "RSA", "key": "atsrv_sig", "use": ["sig"]}]

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', dest='port', default=80, type=int)
    parser.add_argument('-t', dest='tls', action='store_true')
    parser.add_argument('-f', dest='fdir', required=True)
    args = parser.parse_args()

    folder = os.path.abspath(os.curdir)

    if args.port:
        _host = "{}:{}".format(HOST, args.port)
    else:
        _host = HOST

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

    _kj = build_keyjar(KEY_DEF)[1]
    value_conv = JWSProducer(_host, sign_keys=_kj, sign_alg="RS256")

    cherrypy.tree.mount(AttestationService(args.fdir, value_conv), '/',
                        provider_config)

    # If HTTPS
    if args.tls:
        cherrypy.server.ssl_certificate = SERVER_CERT
        cherrypy.server.ssl_private_key = SERVER_KEY
        if CA_BUNDLE:
            cherrypy.server.ssl_certificate_chain = CA_BUNDLE

    cherrypy.engine.start()
    cherrypy.engine.block()
