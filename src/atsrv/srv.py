import cherrypy
import logging

from atsrv.attestation_service import AttestationServer
from jwkest import as_bytes

logger = logging.getLogger('')


class AttestationService(object):
    def __init__(self, fdir, value_conv):
        self.attestation_srv = AttestationServer(fdir, value_conv)

    @cherrypy.expose
    def entity(self, token_id=''):
        try:
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            return as_bytes(self.attestation_srv[token_id])
        except KeyError:
            cherrypy.HTTPError('Non existent Token ID')

    def _cp_dispatch(self, vpath):
        # Only get here if vpath != None
        ent = cherrypy.request.remote.ip
        logger.info('ent:{}, vpath: {}'.format(ent, vpath))

        if len(vpath) == 1:
            cherrypy.request.params['token_id'] = vpath.pop(0)
            return self.entity

        return self.entities

    @cherrypy.expose
    def entities(self):
        return as_bytes(self.attestation_srv.sign_db())
