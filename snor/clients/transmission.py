import transmissionrpc
from . import BaseCLient


class Client(BaseCLient):
    _name = 'transmission'
    _settings = {
        'port': 9091,
        'address': 'localhost',
        'user': None,
        'password': None
    }

    def add_magnet_hash(self, magnet_hash, download_dir):
        c = transmissionrpc.Client(**self.get_settings())
        url = 'magnet:?xt=urn:btih:{h}'.format(h=magnet_hash)
        return c.add_torrent(url, download_dir=download_dir)

    def get_completed(self):
        print 'Completed'

    def is_active(self):
        try:
            transmissionrpc.Client(**self.get_settings())
        except:
            return False
        return True
