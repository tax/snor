import os
import peewee
import requests
from datetime import datetime
import xml.etree.cElementTree as et


WANTED = 0
FOUND = 1
DOWNLOADING = 2
DOWNLOADED = 3
SKIPPED = 4
API_KEY = '103048D30C58E1F3'

VIDEO_EXTENSIONS = (
    'avi', 'mkv', 'mpg', 'mpeg', 'wmv', 'ogm', 'mp4',
    'iso', 'img', 'divx', 'm2ts', 'm4v', 'ts', 'flv',
    'f4v', 'mov', 'rmvb', 'vob', 'dvr-ms', 'wtv', 'ogv',
    '3gp'
)

dirname = os.path.dirname(__file__)
db = peewee.SqliteDatabase('snor_database.db')


class Show(peewee.Model):
    tvdb_id = peewee.IntegerField(unique=True)
    seriesname = peewee.CharField()
    status = peewee.CharField()
    folder = peewee.CharField()
    network = peewee.CharField(null=True)
    language = peewee.CharField(null=True)
    overview = peewee.TextField(null=True)
    filters = peewee.TextField(null=True)
    imdb_id = peewee.CharField(null=True)
    zap2it_id = peewee.CharField(null=True)
    date_added = peewee.DateTimeField(default=datetime.now)
    date_updated = peewee.DateTimeField(null=True)
    firstaired = peewee.DateTimeField(null=True)
    date_last_updated = peewee.DateTimeField(default=datetime.now)
    airs_time = peewee.CharField(null=True)
    airs_dayofweek = peewee.CharField(null=True)
    is_active = peewee.BooleanField(default=True)
    use_season_folders = peewee.BooleanField(default=False)

    def check_download_status(self):
        vids = []

        episodes = Episode.select().where(
            Episode.show == self,
            Episode.status != DOWNLOADED
        )

        if episodes.count() != 0:
            for root, dirs, files in os.walk(self.folder):
                files = [os.path.join(root, f) for f in files]
                # Only copy video files
                vids.extend(
                    filter(lambda x: x.lower().endswith(VIDEO_EXTENSIONS), files)
                )

        for e in episodes:
            l = lambda x: e.get_code() in os.path.basename(x).upper() or \
                e.get_code(short=True) in os.path.basename(x).upper()
            found = filter(l, vids)
            if found:
                e.location = found[0]
                e.status = DOWNLOADED
                e.save()

    def save_episodes(self, skip=False, skip_specials=False):
        status = WANTED
        if skip:
            status = SKIPPED

        for episode in self._get_episodes():
            # Only create episode if it doesn't exist
            eps = Episode.select().where(Episode.tvdb_id == episode['tvdb_id'])
            if eps.count() == 0:
                Episode.create(
                    show=self,
                    status=status,
                    **episode
                )
            else:
                episode_id = list(eps)[0].id
                Episode.update(**episode)\
                    .where(Episode.id == episode_id).execute()

        #After saving mark unaired episodes as wanted
        if skip:
            Episode.update(status=WANTED).where(
                Episode.status == SKIPPED,
                Episode.show == self,
                Episode.firstaired > datetime.now()
            ).execute()

        if skip_specials:
            Episode.update(status=SKIPPED).where(
                Episode.seasonnumber == 0,
                Episode.show == self,
            ).execute()

    def _get_episodes(self):
        result = []
        url = 'http://thetvdb.com/api/{api_key}/series/{id}/all/'
        r = requests.get(url.format(id=self.tvdb_id, api_key=API_KEY))
        tree = et.fromstring(r.content)
        # Only use valid keys
        vk = Episode._meta.fields.keys()
        for ch in tree.findall('Episode'):
            e = {i.tag.lower(): i.text for i in ch if i.tag.lower() in vk}
            e['tvdb_id'] = e['id']
            del e['id']
            result.append(e)
        return result

    def __unicode__(self):
        return self.seriesname

    class Meta:
        database = db


class Episode(peewee.Model):
    tvdb_id = peewee.IntegerField(unique=True)
    imdb_id = peewee.CharField(null=True)
    episodename = peewee.CharField(null=True)
    location = peewee.CharField(null=True)
    seasonnumber = peewee.IntegerField()
    episodenumber = peewee.IntegerField()
    overview = peewee.TextField(null=True)
    firstaired = peewee.DateTimeField(null=True)
    date_added = peewee.DateTimeField(default=datetime.now)
    date_last_updated = peewee.DateTimeField(default=datetime.now)
    magnet_hash = peewee.CharField(null=True)
    status = peewee.IntegerField(default=0)
    show = peewee.ForeignKeyField(Show)

    def get_status(self):
        s = ['wanted', 'found', 'downloading', 'downloaded', 'skipped']
        if self.status not in [DOWNLOADED, DOWNLOADING]:
            if not self.firstaired or self.firstaired > datetime.now():
                return 'not aired'
        return s[self.status]

    def get_magnet_link(self):
        return 'magnet:?xt=urn:btih:{h}'.format(h=self.magnet_hash)

    def get_download_dir(self):
        directory = self.show.folder.rstrip('/')
        if self.show.use_season_folders:
            se = self.seasonnumber
            if se < 10:
                directory += '/Season 0{s}'.format(s=se)
            else:
                directory += '/Season {s}'.format(s=se)
        return directory

    def get_code(self, short=False):
        ep = self.episodenumber
        se = self.seasonnumber
        if ep < 10:
            ep = '0{e}'.format(e=ep)
        if short:
            return '{s}{e}'.format(s=se, e=ep)
        if se < 10:
            se = '0{s}'.format(s=se)
        return 'S{s}E{e}'.format(s=se, e=ep)

    def __unicode__(self):
        return '{s}: {e} {c}'.format(
            s=self.show.seriesname,
            e=self.episodename,
            c=self.get_code()
        )

    class Meta:
        database = db


class Setting(peewee.Model):
    name = peewee.CharField(null=True)
    value = peewee.TextField(null=True)
    date_added = peewee.DateTimeField(default=datetime.now)
    date_last_updated = peewee.DateTimeField(default=datetime.now)

    def __unicode__(self):
        return self.name

    class Meta:
        database = db
