# -*- coding: utf-8 -*-
"""
Initialize Flask app

"""
import os, sys
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager
from flask.ext.login import LoginManager

reload(sys)
sys.setdefaultencoding('utf-8')

app = Flask(__name__)
app.config.from_object('apps.settings.Production')

# login manager
##############################################################################################################
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'
login_manager.login_message = u'로그인이 필요합니다.'
##############################################################################################################



# error logging
##############################################################################################################
ERROR_LOG_DIR = './log/'
app.config['ERROR_LOG_DIR'] = ERROR_LOG_DIR

if not app.debug:
	import logging
	file_handler = logging.FileHandler(os.path.join(app.root_path, app.config['ERROR_LOG_DIR'], "log.txt"))
	#file_handler = logging.handlers.TimedRotatingFileHandler(os.path.join(app.root_path, app.config['ERROR_LOG_DIR'], "log.txt"))
	file_handler.setLevel(logging.ERROR)
	app.logger.addHandler(file_handler)
##############################################################################################################


# db and migrate setting
##############################################################################################################
db = SQLAlchemy(app)
manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)
##############################################################################################################

import controllers, models

