import os
import sys
import signal
import time
import ctypes
import itertools
import string
import platform
import threading
import json
import datetime
import xml.etree.cElementTree as et
import requests
import search
import clients
import logging
import models
from models import Episode, Show, Setting
from conf import settings


logger = logging.getLogger('snor_log')
API_KEY = '103048D30C58E1F3'
IS_WINDOWS = 'Windows' in platform.system()
DB_NAME = 'snor_database.db'


def find_shows(q):
    url = 'http://thetvdb.com/api/GetSeries.php?seriesname={q}'
    logger.info(url.format(q=q))
    r = requests.get(url.format(q=q))
    t = et.fromstring(r.content)
    return [{i.tag.lower(): i.text for i in c} for c in t.findall('Series')]


def save_show(choice='new', **kwargs):
    # Convert to boolean
    kwargs['use_season_folders'] = 'use_season_folders' in kwargs

    # Download serie info from tvdb
    url = 'http://thetvdb.com/api/{api_key}/series/{id}/'

    r = requests.get(url.format(id=kwargs['tvdb_id'], api_key=API_KEY))
    t = et.fromstring(r.content)
    show = {i.tag.lower(): i.text for i in t.find('Series')}

    # Only create show in db if it doesn't exist
    shows = Show.select().where(Show.tvdb_id == kwargs['tvdb_id'])
    if shows.count() == 0:
        s = Show.create(**dict(kwargs.items() + show.items()))
    else:
        s = list(shows)[0]
        # Only use valid keys
        vk = Show._meta.fields.keys()
        d = {k: v for k, v in dict(kwargs.items() + show.items()).items() if k in vk}
        d['tvdb_id'] = d['id']
        del d['id']
        d['date_last_updated'] = datetime.datetime.now()
        s.update(**d).execute()

    s.save_episodes('download_new_only' in kwargs)

    # Mark episodes as downloaded if they exist
    if choice == 'existing':
        s.check_download_status()

    return s.id


def process_search_torrent():
    res = []
    eps = Episode.select().join(Show).where(
        Show.is_active == True,
        Episode.status == models.WANTED,
        Episode.firstaired < datetime.datetime.now()
    )

    for e in eps:
        c = search.get_search_client(settings.search_client)
        torrents = c.search(e.show.seriesname, e.get_code())

        # Create default filters for episode code
        fns = [{'key': 'name', 'value': e.get_code(), 'operator': 'in'}]
        # Add filters from show settings
        fns.extend(json.loads(e.show.filters))
        filters = [build_filter(**f) for f in fns
                   if f['key'] in c.valid_filters]
        for fl in filters:
            torrents = filter(fl, torrents)

        msg = {'msg': 'No hash found for {e}'.format(e=e), 'stat': 'fail'}
        if len(torrents) > 0:
            e.magnet_hash = torrents[0]['hash']
            e.status = models.FOUND
            e.save()
            msg['msg'] = 'Saved hash for {e}'.format(e=e)
            msg['stat'] = 'ok'
        res.append(msg)

    return res


def process_download_torrent():
    res = []
    eps = Episode.select().join(Show).where(
        Show.is_active == True,
        Episode.status == models.FOUND
    )
    tc = clients.get_torrent_client(settings.client)
    for e in eps:
        try:
            tc.add_magnet_hash(e.magnet_hash, e.get_download_dir())
            e.status = models.DOWNLOADING
            e.save()
            res.append({
                'msg': 'Started downloading {e}'.format(e=e),
                'stat': 'ok'
            })
        except Exception, ex:
            res.append({
                'msg': 'Failed to add {e} to client: {ex}'.format(e=e, ex=ex),
                'stat': 'fail'
            })
    return res


def process_check_downloaded():
    shows = Show.select().join(Episode).where(
        Episode.status == models.WANTED,
        Episode.firstaired < datetime.datetime.now()
    ).group_by(Show)
    return [s.check_download_status() for s in shows]


def process_check_new_episodes():
    res = []
    # Only check after 24 hours
    yesterday = datetime.datetime.now() - datetime.timedelta(1)
    shows = Show.select().where(
        Show.date_last_updated > yesterday
    )
    for s in shows:
        res.append(save_show(tvdb_id=s.tvdb_id))
    return res


def build_filter(key, value, operator):

    if operator == 'eq':
        return lambda x: x[key] == value
    if operator == 'ne':
        return lambda x: x[key] != value
    if operator == 'gt':
        return lambda x: x[key] > value
    if operator == 'st':
        return lambda x: x[key] < value
    if operator == 'in':
        return lambda x: value.lower() in x[key].lower()
    if operator == 'not_in':
        return lambda x: value.lower() not in x[key].lower()
    if operator == 'startswith':
        return lambda x: value.lower().startswith(x[key].lower())
    if operator == 'not_startswith':
        return lambda x: not value.lower().startswith(x[key].lower())


def list_directory(current):
    res = {
        'result': [],
        'current': current,
        'selectable': True,
        'stat': 'ok'
    }

    if IS_WINDOWS and current == '/':
        for d in get_available_drives():
            f = {'path': d + ':\\', 'name': d + ':\\', 'is_dir': True}
            res['result'].append(f)
            res['selectable'] = False
        return res

    path = os.path.abspath(os.path.join(current, os.pardir))
    if len(current) == 3 and current.endswith(':\\'):
        path = '/'
        f = {'path': path, 'name': '..', 'is_dir': True}
        res['result'].append(f)
    elif current != '/':
        f = {'path': path, 'name': '..', 'is_dir': True}
        res['result'].append(f)

    try:
        for item in os.listdir(current):
            f = {
                'path': os.path.join(current, item),
                'name': item,
                'is_dir': os.path.isdir(os.path.join(current, item))
            }
            res['result'].append(f)
    except:
        res['selectable'] = False
        res['msg'] = 'Could not open this directory'
        res['stat'] = 'fail'
    return res


def get_available_drives():
    if not IS_WINDOWS:
        return []
    drive_bitmask = ctypes.cdll.kernel32.GetLogicalDrives()
    return list(
        itertools.compress(
            string.ascii_uppercase,
            map(lambda x: ord(x) - ord('0'), bin(drive_bitmask)[:1:-1])
        )
    )


def create_database(destroy_existing=False):
    """ Create db and tables if it doesn't exist """
    if not os.path.exists(DB_NAME):
        logger.info('Create database: {0}'.format(DB_NAME))
        open(DB_NAME, 'a').close()
        Show.create_table()
        Episode.create_table()
        Setting.create_table()


class Tasks(threading.Thread):
    def __init__(self, tasks, seconds, host, port):
        threading.Thread.__init__(self)
        self.quit = False
        self.tasks = tasks
        self.seconds = seconds
        self.host = host
        self.port = port

    def run(self):
        counter = 0
        while not self.quit:
            if counter == self.seconds:
                counter = 0
                logger.info('Run background tasks')
                for t in self.tasks:
                    url = 'http://{host}:{port}/api/?action={task}'
                    url = url.format(task=t, host=self.host, port=self.port)
                    r = requests.post(url)
                    logger.info(r.content)
            counter += 1
            time.sleep(1)
        logger.info('Quit running background tasks')

    def stop(self):
        self.quit = True


def start_background_tasks(host, port):
    # Start background tasks to search and download
    tasks = [
        'background_search', 'background_download',
        'background_status', 'background_update'
    ]
    t = Tasks(tasks, host=host, port=port, seconds=5 * 30)
    t.start()

    def signal_exit(signal, frame):
        t.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_exit)
