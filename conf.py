import os
import clients
import search
import json



class Conf():
    _filename = 'settings.json'
    _settings = {
        'login_required' : False,
        'username' : 'admin',
        'password' : 'admin',
        'filters' : '',
        'secret_key' : os.urandom(24).encode('base64'),
        'folder' : os.path.expanduser('~'),
        'client' : clients.get_torrent_clients()[0],
        'search_client' : search.get_search_clients()[0],
        'use_season_folders' : True,
        'download_new_only' : False
    }

    def __getattr__(self, name):
        settings = self.get_settings()
        return settings[name]

    def get_settings(self):
        try:
            with open(self._filename, 'r') as f:
                return json.loads(f.read())
        except:
            with open(self._filename, 'w+') as f:
                f.write(json.dumps(self._settings))
            return self._settings

    def set_settings(self, **kwargs):
        # Only copy valid keys fallback to default settings
        vk = self._settings.keys()
        kwargs = { k:v for k,v in kwargs.items() if k in vk }
        kwargs = dict(self._settings.items() + kwargs.items())
        with open(self._filename, 'w+') as f:
            f.write(json.dumps(kwargs))

settings = Conf()
