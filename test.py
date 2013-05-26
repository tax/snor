import unittest
import os
import requests
import snor
import snor.conf as conf
import snor.clients as clients


class TestSettings(unittest.TestCase):
    def setUp(self):
        if os.path.exists('settings.json'):
            os.remove('settings.json')

    def test_non_existing(self):
        c = conf.Conf()
        self.assertRaises(KeyError, lambda : c.doesnotexist)

    def test_save(self):
        c = conf.Conf()
        d = { 'username':'u', 'password':'p' }
        self.assertFalse(os.path.exists('settings.json'))
        c.set_settings(**d)
        self.assertEqual(c.username, 'u')
        self.assertEqual(c.password, 'p')
        self.assertFalse(c.login_required)
        self.assertTrue(os.path.exists('settings.json'))

class TestSite(unittest.TestCase):
    def setUp(self):
        self.app = snor.app.test_client()
        #Go back to default settings
        if os.path.exists('settings.json'):
            os.remove('settings.json')

    def test_empty_list(self):
        r = self.app.get('/')
        self.assertIn("You dont have any shows in your", r.data)

    def test_login_not_required(self):
        #r = requests.get(self.url)
        r = self.app.get('/')
        self.assertIn('Welcome to snor', r.data) 
        
    def test_login_required(self):
        d = { 'login_required':'login' }
        # Save settings to require login
        self.app.post('/settings/', data=d)
        r = self.app.get('/', follow_redirects=True)
        self.assertIn('Please sign in', r.data) 
        # Login with default password and username
        r = self.app.post('/login/', data={
            'username':'admin', 'password':'admin'
        }, follow_redirects=True)        
        self.assertIn('Welcome to snor', r.data) 
        # Logout again
        r = self.app.get('/logout/', follow_redirects=True)        
        self.assertIn('Logged out', r.data) 
        self.assertIn('Please sign in', r.data) 


class TestClients(unittest.TestCase):

    def setUp(self):
        # Remove settings files
        for f in ['transmission','utorrent']:
            filename = 'settings.{n}.json'.format(n=f)
            try:
                os.remove(filename)
            except:
                pass

    def test_get_clients(self):
        cs = clients.get_torrent_clients()
        self.assertItemsEqual(cs, ['transmission','utorrent'])

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


    def test_client_save_settings_files(self):
        filename = 'settings.transmission.json'
        c = clients.get_torrent_client('transmission')

        self.assertFalse(
            os.path.exists(filename),
            'File should not exist if we start test'
        )

        old = c.get_settings()      
        
        new = old.copy()
        new['address'] = 'domain.com'
        c.set_settings(**new)
        self.assertTrue(
            os.path.exists(filename),
            'File should exist if we save settings'
        )

        c.set_settings(**old)
        self.assertFalse(
            os.path.exists(filename),
            'File should be removed if we go back to default settings'
        )
        
        #self.assertEqual(new, c.get_settings())

    # def test_client_settings_default_nofile(self):
    #     c = clients.get_torrent_client('transmission')
    #     old = c.get_settings()      
    #     new = old
    #     new['address'] = 'domain.com'
    #     self.assertEqual(c._settings, old)
    #     c.set_settings(**new)
    #     self.assertEqual(old, c.get_settings())
    #     c.set_settings(**old)

    # def test_choice(self):
    #     element = random.choice(self.seq)
    #     self.assertTrue(element in self.seq)

    # def test_sample(self):
    #     with self.assertRaises(ValueError):
    #         random.sample(self.seq, 20)
    #     for element in random.sample(self.seq, 5):
    #         self.assertTrue(element in self.seq)

if __name__ == '__main__':
    unittest.main()

# c = clients.get_torrent_client('transmission')
# print c.get_settings()
# d = {
#     'port': 9091,
#     'address':'localhost', 
#     'user':None,
#     'password':None
# }
# c.save_settings(**d)

# print c.get_settings()
# print c._name


#c.get_completed()