import json
import logging
import os
import time

from oic.utils.jwt import JWT

logger = logging.getLogger(__name__)


class JWSProducer(object):
    def __init__(self, iss, sign_keys, sign_alg):
        self.iss = iss
        self.sign_keys = sign_keys
        self.sign_alg = sign_alg

    def create_jws(self, val):
        """
        Create signed JSON Web Token

        :param val: dictionary
        :return: Signed JWT
        """
        _jwt = JWT(self.sign_keys, iss=self.iss, sign_alg=self.sign_alg)
        return _jwt.pack(spec=val)

    def __call__(self, val):
        """

        :param val: Should be a JSON document
        :return: Signed JWT with the JSON document as body
        """

        # make sure it's a JSON document
        try:
            _data = json.loads(val)
        except Exception:
            raise

        return self.create_jws(_data)


class AttestationServer(object):
    def __init__(self, fdir, value_conv=None):
        self.fdir = fdir
        self.fmtime = {}
        self.db = {}
        self.value_conv = value_conv
        if not os.path.isdir(fdir):
            os.makedirs(fdir)

    def __getitem__(self, item):
        if self.is_changed(item):
            logger.info("File content change in {}".format(item))
            fname = os.path.join(self.fdir, item)
            self.db[item] = self._read_info(fname)

        return self.db[item]

    def keys(self):
        self.sync()
        for k in self.db.keys():
            yield k

    @staticmethod
    def get_mtime(fname):
        try:
            mtime = os.stat(fname).st_mtime_ns
        except OSError:
            # The file might be right in the middle of being written
            # so sleep
            time.sleep(1)
            mtime = os.stat(fname).st_mtime_ns

        return mtime

    def is_changed(self, item):
        fname = os.path.join(self.fdir, item)
        if os.path.isfile(fname):
            mtime = self.get_mtime(fname)

            try:
                _ftime = self.fmtime[item]
            except KeyError:  # Never been seen before
                self.fmtime[item] = mtime
                return True

            if mtime > _ftime:  # has changed
                self.fmtime[item] = mtime
                return True
            else:
                return False
        else:
            logger.error('Could not access {}'.format(fname))
            raise KeyError(item)

    def _read_info(self, fname):
        if os.path.isfile(fname):
            try:
                info = open(fname, 'r').read()
                try:
                    info = self.value_conv(info)
                except KeyError:
                    pass
                return info
            except Exception as err:
                logger.error(err)
                raise
        else:
            logger.error('No such file: {}'.format(fname))
        return None

    def sync(self):
        if not os.path.isdir(self.fdir):
            raise ValueError('No such directory: {}'.format(self.fdir))
        for f in os.listdir(self.fdir):
            fname = os.path.join(self.fdir, f)
            if f in self.fmtime:
                if self.is_changed(f):
                    self.db[f] = self._read_info(fname)
            else:
                mtime = self.get_mtime(fname)
                self.db[f] = self._read_info(fname)
                self.fmtime[f] = mtime

    def items(self):
        self.sync()
        for k, v in self.db.items():
            yield k, self.value_conv(v)

    def dict(self):
        return dict([(k,v) for k,v in self.db.items()])

    def sign_db(self):
        return self.value_conv.create_jws(self.dict())
