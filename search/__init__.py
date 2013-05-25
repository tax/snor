import os
import json

class BaseCLient():
    _name = 'base'
    _result_keys = ['size','seeds','peers']

    def __init__(self):
        """
        Dont initialize client because it could raise an error 
        """
        pass  

    @property
    def valid_filters(self):
        """
        Returns list with valid filter keys name and hash are mandatory.
        """
        return self._result_keys.append(['name','hash'])

    def search(self, show_name, episode_code):        
        """
        Returns a list with dicts with the search results .

        Dict must contain the keys returned by `valid_filters`

        :param show_name: The name of the show to search for
        :param episode_code: The episode en season number (Ex. S01E12).
        """
        raise NotImplementedError

    def is_active(self):
        raise NotImplementedError        


def get_search_client(client_name):
    module = 'search.' + client_name
    try:
        m = __import__(module, globals(), locals(), ['Client'], -1)
        client = m.Client()
        return client
    except ImportError,ex:
        msg = 'Could not load search client {c}'.format(c=client_name)
        raise ImportError(msg)

def get_search_clients():
    files = []
    for f in os.listdir(os.curdir + '/search'):
        if f.endswith('.py') and f != '__init__.py':
            files.append(f[:-3])
    return files

