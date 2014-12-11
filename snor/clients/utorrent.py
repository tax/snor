import requests
import re
from . import BaseCLient


class Client(BaseCLient):
    _name = 'utorrent'
    _settings = {
        'port': 61137,
        'address': 'localhost',
        'user': 'admin',
        'password': 'password'
    }

    def add_magnet_hash(self, magnet_hash, download_dir):
        auth = (self._settings['user'], self._settings['password'])
        url = 'http://{address}:{port}/gui/'.format(**self._settings)
        r = requests.get(url + 'token.html', auth=auth)
        cookie = r.cookies
        # Extract token
        token_re = "<div id='token' style='display:none;'>([^<>]+)</div>"
        match = re.search(token_re, r.content)
        token = match.group(1)

        #Set to correct download folder
        p = {
            'token': token,
            'action': 'setsetting',
            's': 'dir_completed_download',
            'v': download_dir
        }
        r = requests.get(url, params=p, auth=auth, cookies=cookie)
        p = {
            'token': token,
            'action': 'setsetting',
            's': 'dir_completed_download_flag',
            'v': '1'
        }
        requests.get(url, params=p, auth=auth, cookies=cookie)
        # Add magnet hash
        magnet_url = 'magnet:?xt=urn:btih:{0}'.format(magnet_hash)
        p = {'token': token, 'action': 'add-url', 's': magnet_url}
        r = requests.get(url, params=p, auth=auth, cookies=cookie)

    def get_completed(self):
        print 'Completed'

    def is_active(self):
        return True
