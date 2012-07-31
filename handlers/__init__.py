# -*- coding: utf-8 -*-
'''
Created on Mar 13, 2012

@author: moloch

    Copyright [2012] [Redacted Labs]

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
'''


import sys
import models
import logging

from time import sleep
from os import urandom, path
from base64 import b64encode
from models import dbsession
from modules.Menu import Menu
from libs.ConsoleColors import *
from libs.Session import SessionManager
from libs.HostIpAddress import HostIpAddress
from libs.AuthenticateReporter import scoring_round
from tornado import netutil
from tornado import process
from tornado import options
from tornado.web import Application
from tornado.web import StaticFileHandler
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop, PeriodicCallback
from handlers.BoxHandlers import *
from handlers.UserHandlers import *
from handlers.AdminHandlers import *
from handlers.ErrorHandlers import *
from handlers.PublicHandlers import *
from handlers.HashesHandlers import *
from handlers.SocialHandlers import *
from handlers.CrackMeHandlers import *
from handlers.ReporterHandlers import *
from handlers.PastebinHandlers import *
from handlers.PastebinHandlers import *
from handlers.WebsocketHandlers import *
from handlers.ChallengeHandlers import *
from handlers.ScoreboardHandlers import *


config = ConfigManager.Instance()
app = Application([
                  # Static Handlers - Serves static CSS, JavaScript and
                  # image files
                  (r'/static/(.*)',
                   StaticFileHandler, {'path': 'static'}),
                  (r'/avatars/(.*)',
                   StaticFileHandler, {'path': 'files/avatars'}),

                  # Reporter Handlers - Communication with reporters
                  (r'/reporter/register', ReporterRegistrationHandler, {
                   'dbsession': dbsession}),

                  # User Handlers - Serves user related pages
                  (r'/user/shares/download(.*)', ShareDownloadHandler, {
                   'dbsession': dbsession}),
                  (r'/user/shares',
                   ShareUploadHandler, {'dbsession': dbsession}),
                  (r'/user/settings(.*)',
                   SettingsHandler, {'dbsession': dbsession}),
                  (r'/user/team/ajax(.*)',
                   TeamAjaxHandler, {'dbsession': dbsession}),
                  (r'/user/team',
                   TeamViewHandler, {'dbsession': dbsession}),
                  (r'/user/logout',
                   LogoutHandler, {'dbsession': dbsession}),
                  (r'/user/reporter',
                   ReporterHandler, {'dbsession': dbsession}),
                  (r'/user', HomeHandler, {'dbsession': dbsession}),

                  # Box Handlers - Serves box related pages
                  (r'/boxes(.*)',
                   BoxesViewHandler, {'dbsession': dbsession}),

                  # Crack Me Handlers - Serves crack me related pages
                  (r'/crackme/download(.*)', CrackMeDownloadHandler, {
                   'dbsession': dbsession}),
                  (r'/crackme(.*)',
                   CrackMeHandler, {'dbsession': dbsession}),

                  # Hashes Handlers - Serves hash related pages
                  (r'/hashes',
                   HashesHandler, {'dbsession': dbsession}),
                  (r'/hashes/ajax(.*)',
                   HashesAjaxHandler, {'dbsession': dbsession}),
                  (r'/wallofsheep',
                   WallOfSheepHandler, {'dbsession': dbsession}),

                  # Scoreboard Handlers - Severs scoreboard related
                  # pages
                  (r'/scoreboard',
                   ScoreBoardHandler, {'dbsession': dbsession}),
                  (r'/all_time(.*)',
                   AllTimeHandler, {'dbsession': dbsession}),
                  (r'/pie_chart(.*)',
                   PieChartHandler, {'dbsession': dbsession}),
                  (r'/bar_chart(.*)',
                   BarChartHandler, {'dbsession': dbsession}),

                  # Challenges Handlers
                  (r'/challenges/ajax(.*)', ChallengesAjaxHandler, {
                   'dbsession': dbsession}),
                  (r'/challenges',
                   ChallengesHandler, {'dbsession': dbsession}),

                  # Social Challenges Handlers
                  (r'/se(.*)',
                   SocialHomeHandler, {'dbsession':dbsession}),

                  # Admin Handlers - Administration pages
                  (r'/admin/create/(.*)',
                   AdminCreateHandler, {'dbsession':dbsession}),
                  (r'/admin/edit/(.*)',
                   AdminEditHandler, {'dbsession':dbsession}),
                  (r'/admin/notify', AdminNotifyHandler),
                  (r'/admin/notify/ajax(.*)', AdminAjaxNotifyHandler, {
                   'dbsession', dbsession}),

                  # WebSocket Handlers - Websocket communication
                  # handlers
                  (r'/websocket', WebsocketHandler),

                  # Pastebin Handlers
                  (r'/pastebin',
                   PastebinHandler, {'dbsession':dbsession}),
                  (r'/pastebin/view(.*)',
                   DisplayPostHandler, {'dbsession':dbsession}),
                  (r'/pastebin/delete(.*)',
                   DeletePostHandler, {'dbsession':dbsession}),

                  # Root handlers - Serves all public pages
                  (r'/login', LoginHandler),
                  (r'/registration', UserRegistraionHandler,
                   {'dbsession': dbsession}),
                  (r'/about', AboutHandler),
                  (r'/', HomePageHandler),

                  # Error handlers - Serves error pages
                  (r'/403', UnauthorizedHandler),
                  (r'/(.*).php', PhpHandler),
                  (r'/(.*)', NotFoundHandler)
                  ],

    # Randomly generated secret key
    cookie_secret=b64encode(urandom(64)),

    # Ip addresses that access the admin interface
    admin_ips=config.admin_ips,

    # Template directory
    template_path = 'templates',

    # Request that does not pass @authorized will be
    # redirected here
    forbidden_url = '/403',

    # Requests that does not pass @authenticated  will be
    # redirected here
    login_url = '/login',

    # UI Modules
    ui_modules = {"Menu": Menu},

    # Enable XSRF forms
    xsrf_cookies = True,

    # Recaptcha Settings
    recaptcha_enable = config.recaptcha_enable,
    recaptcha_private_key = config.recaptcha_private_key,

    # WebSocket Host IP Address
    ws_ip_address = config.ws_ip_address,
    ws_port = config.listen_port,

    # Special file directories
    avatar_dir = path.abspath('files/avatars/'),
    crack_me_dir = path.abspath('files/crack_mes/'),
    shares_dir = path.abspath('files/shares/'),
    se_dir = path.abspath('files/se/'),

    # Milli-Seconds between scoring
    ticks = int(60 * 1000),

    # Milli-Seconds between session clean up
    clean_up_timeout = int(60 * 1000),

    # Debug mode
    debug = config.debug,

    # Application version
    version = '0.2'
)

# Main Functions
def cache_actions():
    ''' Loads all of the actions from the database into memory for the scoreboard pages'''
    action_list = dbsession.query(models.Action).all()
    ws_manager = WebSocketManager.Instance()
    for action in action_list:
        team = dbsession.query(
            models.User).filter_by(id=action.user_id).first()
        score_update = ScoreUpdate(
            action.created.strftime("%d%H%M%S"), action.value, team.team_name)
        ws_manager.cachedScores.add_score(score_update)

# Main entry point
def start_game():
    ''' Main entry point for the application '''
    cache_actions()
    sockets = netutil.bind_sockets(config.listen_port)
    server = HTTPServer(app)
    server.add_sockets(sockets)
    io_loop = IOLoop.instance()
    session_manager = SessionManager.Instance()
    if process.task_id() == None:
        scoring = PeriodicCallback(
            scoring_round, app.settings['ticks'], io_loop=io_loop)
        session_clean_up = PeriodicCallback(session_manager.clean_up,
            app.settings['clean_up_timeout'], io_loop=io_loop)
        scoring.start()
        session_clean_up.start()
    try:
        for count in range(3, 0, -1):
            sys.stdout.write(
                "\r" + INFO + "The game will begin in ... %d" % (count,))
            sys.stdout.flush()
            sleep(1)
        sys.stdout.write("\r" + INFO + "The game has begun, good hunting!\n")
        sys.stdout.flush()
        io_loop.start()
    except KeyboardInterrupt:
        if process.task_id() == None:
            print('\r' + WARN + 'Shutdown Everything!')
            session_clean_up.stop()
            io_loop.stop()
