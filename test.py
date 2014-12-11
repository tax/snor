import unittest
from snor.utils import create_database
from snor.models import Show, Episode, Setting
import snor.server as server
import snor.conf as conf
import snor.clients as clients


def reset_database():
    Show.delete().execute()
    Episode.delete().execute()
    Setting.delete().execute()

class TestSettings(unittest.TestCase):
    def setUp(self):
        create_database()
        reset_database()

    def test_non_existing(self):
        c = conf.Conf()
        self.assertRaises(KeyError, lambda: c.doesnotexist)

    def test_save(self):
        c = conf.Conf()
        d = {'username': 'u', 'password': 'p'}
        c.set_settings(**d)
        self.assertEqual(c.username, 'u')
        self.assertEqual(c.password, 'p')
        self.assertFalse(c.login_required)


class TestSite(unittest.TestCase):
    def setUp(self):
        create_database()
        reset_database()
        self.app = server.app.test_client()

    def test_empty_list(self):
        r = self.app.get('/')
        self.assertIn("You dont have any shows in your", r.data)

    def test_login_not_required(self):
        #r = requests.get(self.url)
        r = self.app.get('/')
        self.assertIn('Welcome to snor', r.data)

    def test_login_required(self):
        d = {'login_required': 'login'}
        # Save settings to require login
        self.app.post('/settings/', data=d)
        r = self.app.get('/', follow_redirects=True)
        self.assertIn('Please sign in', r.data)
        # Login with default password and username
        r = self.app.post(
            '/login/',
            data={
                'username': 'admin', 'password': 'admin'
            },
            follow_redirects=True
        )
        self.assertIn('Welcome to snor', r.data)
        # Logout again
        r = self.app.get('/logout/', follow_redirects=True)
        self.assertIn('Logged out', r.data)
        self.assertIn('Please sign in', r.data)


class TestClients(unittest.TestCase):
    def setUp(self):
        create_database()
        reset_database()

    def test_get_clients(self):
        cs = clients.get_torrent_clients()
        self.assertItemsEqual(cs, ['transmission', 'utorrent'])

    def test_client_notexsit(self):
        self.assertRaises(
            ImportError,
            clients.get_torrent_client,
            'notexist'
        )

    def test_client_settings(self):
        c = clients.get_torrent_client('transmission')
        self.assertEqual(c._name, 'transmission')
        self.assertEqual(c._settings, c.get_settings())

    def test_client_save_settings(self):
        c = clients.get_torrent_client('transmission')
        old = c.get_settings()
        new = old.copy()
        new['address'] = 'domain.com'
        self.assertEqual(c._settings, old)
        c.set_settings(**new)
        self.assertEqual(new, c.get_settings())


if __name__ == '__main__':
    unittest.main()
