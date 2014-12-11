import requests
import xml.etree.cElementTree as et
from . import BaseCLient


class Client(BaseCLient):
    name = 'torrentz.eu'

    def search(self, show_name, episode_code):
        result = []
        url = 'http://torrentz.eu/feed?q={0}+{1}'

        r = requests.get(url.format(show_name, episode_code))
        t = et.fromstring(r.content)

        for ch in t.findall('channel/item'):
            d = {item.tag.lower(): item.text for item in ch}

            res = {'name': d['title']}
            split = d['description'].split(' ')
            if len(split) == 9:
                res['size'] = split[1]
                res['hash'] = split[8]
                res['seeds'] = split[4]
                res['peers'] = split[6]

                result.append(res)

        return result
