import requests
from snor.clients import BaseCLient

class Client(BaseCLient):
    _name = 'utorrent'
    _settings = {
        'port': 9091,
        'address':'localhost', 
        'user':None,
        'password':None
    }

    def add_magnet_link(self, url, dowload_dir):
        magnet_url = url
        auth = (self._settings['user'],self._settings['password'])
        url = 'http://{address}:{port}/gui/'.format(**self._settings)
        r = requests.get(url + 'token.html', auth=auth)
        cookie = r.cookies
        # Extract token
        token_re = "<div id='token' style='display:none;'>([^<>]+)</div>"
        match = re.search(token_re, r.content)
        token = match.group(1)

        #Set to correct download folder
        d = download_dir
        p = {'token':token, 'action':'setsetting', 's':'dir_completed_download', 'v':d}
        r = requests.get(url, params=p, auth=auth, cookies=cookie)
        print r.status_code
        p = {'token':token, 'action':'setsetting', 's':'dir_completed_download_flag', 'v':'1'}
        requests.get(url, params=p, auth=auth, cookies=cookie)
        # Add magnet hash
        p = {'token':token, 'action':'add-url', 's':magnet_url}
        requests.get(url, params=p, auth=auth, cookies=cookie)

    def get_completed(self):
        print 'Completed'

    def is_active(self):
        return True
