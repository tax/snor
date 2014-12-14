import transmissionrpc
from . import BaseCLient


class Client(BaseCLient):
    name = 'transmission'
    _settings = {
        'port': 9091,
        'address': '127.0.0.1',
        'user': None,
        'password': None
    }

    def add_magnet_hash(self, magnet_hash, download_dir):
        c = transmissionrpc.Client(**self.get_settings())
        url = 'magnet:?xt=urn:btih:{h}'.format(h=magnet_hash)
        return c.add_torrent(url, download_dir=download_dir)

    def is_active(self):
        try:
            transmissionrpc.Client(**self.get_settings())
        except:
            return False
        return True
