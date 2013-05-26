import os
import time
import urllib
import signal
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps
from flask import Flask
from flask import jsonify, redirect, request, render_template, session, make_response
from conf import settings
from models import *
from utils import *
import clients
import search


LOGFILE_NAME = 'debug.log'
MB = 1024 * 1024 * 1024

app = Flask(__name__)
app.secret_key = str(settings.secret_key)
app.config['LOGGER_NAME'] = 'snor_log'

# Create logger
handler = RotatingFileHandler(LOGFILE_NAME, maxBytes=MB, backupCount=1)
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s\t%(message)s"))
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if settings.login_required and 'username' not in session:
            return redirect('/login/')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login/', methods=['GET','POST'])
def login():
    msg = request.args.get('msg','')
    if request.method == 'POST':
        if not settings.login_required:
            return redirect('/')
        form = request.form.to_dict()
        u = settings.username
        p = settings.password
        if form['username'] == u and form['password'] == p:
            session['username'] = u
            return redirect('/')
        msg = 'Invalid username or password'
    return render_template('login.html', msg=msg)


@app.route('/logout/')
def logout():
    if 'username' in session:
        del session['username']
    return redirect('/login/?msg=Logged out')


@app.route('/')
@login_required
def index():
    return render_template('home.html', shows=list(Show.select()))


@app.route('/log/')
@login_required
def logfile():
    response = make_response(open(LOGFILE_NAME).read())
    response.headers["Content-type"] = "text/plain"
    return response

@app.route('/settings/', methods=['GET','POST'])
@login_required
def configuration():
    c ={
        'clients' : clients.get_torrent_clients(),
        'search_clients' : search.get_search_clients(),
        'settings' : settings
    }

    if request.method == 'POST':
        try:
            new = request.form.to_dict()
            new['login_required'] = new['login_required'] == 'login'
            new['use_season_folders'] = new.has_key('use_season_folders')
            new['download_new_only'] = new.has_key('download_new_only')
            # Dont overwrite secret key
            new['secret_key'] = app.secret_key
            settings.set_settings(**new)        
            c['msg'] = 'Saved settings'
        except Exception,ex:
            c['msg'] = str(ex)
    return render_template('settings.html', **c)


@app.route('/show/add/')
@login_required
def show_add_choice():
    app.logger.info('bla bla bla')   
    print app.logger_name 
    return render_template('show_add_choice.html')


@app.route('/show/<int:show_id>/')
@login_required
def get_show(show_id):
    c = {
        'show' : Show.get(id=show_id),
        'episodes' : Episode.select().join(Show).where(Show.id == show_id)
    }
    return render_template('show.html', **c)

@app.route('/show/<int:show_id>/settings/', methods=['GET', 'POST'])
@login_required
def get_show_settings(show_id):
    s = Show.get(id=show_id)
    c = {
        'show' : s,
        'settings' : settings,
        'choice' : 'saved_show'
    }
    if request.method == 'POST':
        s.folder = request.form['folder']
        s.filters = request.form['filters']
        s.use_season_folders = request.form.has_key('use_season_folders')
        s.save()
        msg = 'Successfully saved settings'
        return redirect('/show/{id}/?msg={msg}'.format(id=show_id, msg=msg))
    return render_template('show_add.html', **c)

@app.route('/show/add/<choice>/', methods=['GET', 'POST'])
@login_required
def search_show(choice):
    if request.method == 'POST' or request.args.has_key('folder'):
        if request.args.has_key('folder'):
            q = os.path.basename(request.args.get('folder',''))
        else:
            q = request.form['q']
        shows = find_shows(q)
        return render_template(
            'search_result.html', 
            result=shows, 
            choice=choice, 
            query=q
        )
    return render_template('search.html', choice=choice)


@app.route('/show/add/<choice>/<int:show_id>/', methods=['GET', 'POST'])
@login_required
def add_show(choice, show_id):
    if request.method == 'POST':
        pk = save_show(choice=choice, **request.form.to_dict())
        return redirect('/show/{id}/'.format(id=pk))
    c ={
        'choice' : choice, 
        'show_id' : show_id,
        'settings' : settings
    }    
    return render_template('show_add.html', **c)


@app.route('/list/dir/')
@login_required
def list_dir():
    res = list_directory(request.args.get('folder',settings.folder))
    return jsonify(**res)


@app.route('/api/', methods=['POST'])
@login_required
def api(**kwargs):
    args = []
    action = request.args.get('action', '')

    def scan_show(show):
        return show.check_download_status()

    def delete_show(show):
        show.delete_instance(recursive=True)

    def update_show(show):
        return save_show(tvdb_id = show.tvdb_id)

    def episode_mark_skipped(episode):
        episode.status = SKIPPED
        episode.save()

    def episode_mark_wanted(episode):
        episode.status = WANTED
        episode.save()


    def episode_mark_downloaded(episode, location):
        episode.status = DOWNLOADED
        episode.location = location
        episode.save()


    actions = {
        'scan' : scan_show,
        'delete' : delete_show,
        'update' : update_show,
        'episode_mark_wanted' : episode_mark_wanted,
        'episode_mark_skipped' : episode_mark_skipped,
        'episode_mark_downloaded' : episode_mark_downloaded,
        'background_search' : process_search_torrent,
        'background_download' : process_download_torrent,
        'background_status' : process_check_downloaded        
    }

    if not actions.has_key(action):
        msg = 'No action named {}'.format(action)
        return jsonify(stat='fail', msg=msg, result=[])    

    if request.args.has_key('show_id'):
        args.append(Show.get(id=request.args['show_id']))
    if request.args.has_key('episode_id'):
        args.append(Episode.get(id=request.args['episode_id']))
    if request.args.has_key('location'):
        args.append(request.args['location'])

    res = actions[action](*args)        
    return jsonify(stat='ok', result=res)

    

    
@app.template_filter('u')
@app.template_filter('urlencode')
def urlencode_filter(s):
    s = s.encode('utf8')
    s = urllib.quote_plus(s)
    return s

def main():
    # Start background tasks to search and download
    #tasks = ['background_search','background_download','background_status']
    #t = Tasks(tasks, 30)
    #t.start()
    # def signal_exit(signal, frame):
    #     t.stop()
    #     sys.exit(0)    

    # signal.signal(signal.SIGINT, signal_exit)


    # Start webserver
    app.debug = True
    #app.run()

    app.run(host='0.0.0.0')
    app.logger.debug('Webserver started')
    #process_download_torrent()

#if __name__ == '__main__':
#    main()