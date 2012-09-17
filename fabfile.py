import ConfigParser
import os
from fabric.api import env, hosts, roles, run, put
from fabric.operations import local
from fabric.contrib.project import upload_project

config = ConfigParser.ConfigParser()
config.readfp(open('fab.ini'))

env.user = config.get('env', 'user')
env.key_filename = [config.get('env', 'key_filename')]
env.hosts = [config.get('env', 'hosts')]

def doc_make():
    os.chdir("docs")
    local("make html")
    os.chdir("..")

def doc_publish():
    put("docs/build/html/*", "/home/egoz/docs/prambanan/")

def package_publish():
    local("python setup.py register -r microvac sdist upload -r microvac")

