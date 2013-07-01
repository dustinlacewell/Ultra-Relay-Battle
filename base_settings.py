import sys
from os.path import dirname, abspath, join

BASE_PATH = dirname(abspath(__file__))
WEB_PATH = join(BASE_PATH, 'web')
URB_PATH = join(BASE_PATH, 'urb')

DEBUG = True
TEMPLATE_DEBUG = DEBUG

AUTH_USER_MODEL = 'players.Player'

ADMINS = (
    ('Dustin Lacewel', 'dlacewell@gmail.com'),
)

MANAGERS = ADMINS

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',

    'urb.characters',
    'urb.gametypes',
    'urb.players',
)

