import os
import json
import datetime
import clients
import search
from models import Setting


class Conf():
    setting_name = 'snor.conf'
    _settings = {
        'login_required': False,
        'username': 'admin',
        'password': 'admin',
        'default_filters': [],
        'secret_key': os.urandom(24).encode('base64'),
        'api_key': os.urandom(24).encode('base64').replace('+', '-'),
        'folder': os.path.expanduser('~'),
        'client': clients.get_torrent_clients()[0],
        'search_client': search.get_search_clients()[0],
        'use_season_folders': True,
        'download_new_only': False
    }

    def __getattr__(self, name):
        settings = self.get_settings()
        if name not in self._settings:
            raise KeyError('Invalid setting: {0}'.format(name))
        return settings.get(name, None)

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

settings = Conf()
