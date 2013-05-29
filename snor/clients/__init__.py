import os
import json

class BaseCLient():
    _settings = {}
    _name = 'base'

    def __init__(self):
        # Dont initialize client because it could raise an error 
        pass  

    def add_magnet_hash(self, hash, dowload_dir):
        raise NotImplementedError

    def get_completed(self):
        raise NotImplementedError

    def is_active(self):
        raise NotImplementedError

    def get_settings(self):
        filename = 'settings.{n}.json'.format(n=self._name)
        try:
            f = open(filename, 'r')
            return json.loads(f.read())
        except:
            pass
        return self._settings

    def set_settings(self, **kwargs):
        filename = 'settings.{n}.json'.format(n=self._name)
        
        # If values vary from default values save to disk
        if kwargs != self._settings:
            f = open(filename, 'w+')
            f.write(json.dumps(kwargs))
        else:
            try:
                os.remove(filename)
            except:
                pass


        


def get_torrent_client(client_name):
    module = 'snor.clients.' + client_name
    try:
        m = __import__(module, globals(), locals(), ['Client'], -1)
        client = m.Client()
        return client
    except ImportError,ex:
        msg = 'Could not load torrent client {c}'.format(c=client_name)
        raise ImportError(msg)

def get_torrent_clients():
    files = []
    dirname = os.path.dirname(__file__)
    for f in os.listdir(dirname):
        if f.endswith('.py') and f != '__init__.py':
            files.append(f[:-3])
    return files

