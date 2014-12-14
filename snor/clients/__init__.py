import os
import json
import datetime
from ..models import Setting


class BaseCLient():
    name = 'base'
    _settings = {}

    def __init__(self):
        # Dont initialize client because it could raise an error
        pass

    @property
    def setting_name(self):
        return 'client.{0}.conf'.format(self.name)

    def add_magnet_hash(self, hash, dowload_dir):
        raise NotImplementedError

    def get_completed(self):
        raise NotImplementedError

    def is_active(self):
        raise NotImplementedError

    def get_settings(self):
        try:
            setting = Setting.get(name=self.setting_name)
            return json.loads(setting.value)
        except:
            Setting.create(
                name=self.setting_name,
                value=json.dumps(self._settings)
            )
        return self._settings

    def set_settings(self, **kwargs):
        # Only copy valid keys fallback to default settings
        vk = self._settings.keys()
        kwargs = {k: v for k, v in kwargs.items() if k in vk}
        kwargs = dict(self._settings.items() + kwargs.items())
        try:
            s = Setting.get(name=self.setting_name)
            s.value = json.dumps(kwargs)
            s.save()
        except:
            Setting.create(
                name=self.setting_name,
                value=json.dumps(kwargs),
                date_last_updated=datetime.datetime.now()
            )


def get_torrent_client(client_name):
    module = 'snor.clients.' + client_name
    try:
        m = __import__(module, globals(), locals(), ['Client'], -1)
        client = m.Client()
        return client
    except ImportError, ex:
        msg = 'Could not load torrent client {c}'.format(c=client_name)
        raise ImportError(msg)


def get_torrent_clients():
    files = []
    dirname = os.path.dirname(__file__)
    for f in os.listdir(dirname):
        if f.endswith('.py') and f != '__init__.py':
            files.append(f[:-3])
    return files
