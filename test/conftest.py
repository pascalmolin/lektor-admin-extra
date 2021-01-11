import os
import pytest
import shutil
import tempfile
import json
import requests
import subprocess
import time
from requests import Session
from urllib.parse import urljoin
from configparser import ConfigParser

def pytest_addoption(parser):
    parser.addini('project', 'path of a the lektor test project')
    parser.addini('packages', 'plugins path to add', 'pathlist')
    parser.addini('port', 'http server port', default='5787')

@pytest.fixture(scope='session')
def project_path(request):
    return request.config.getini('project')

@pytest.fixture(scope='session')
def port(request):
    return int(request.config.getini('port'))

@pytest.fixture(scope='session')
def packages(request):
    return request.config.getini('packages')


@pytest.fixture(scope='session')
def lektorproject(project_path, packages):
    try:
        output_path = tempfile.mkdtemp()
        print(output_path)
        # copy main repo
        print(project_path)
        shutil.copytree(project_path, output_path, dirs_exist_ok=True)
        # add local modifications
        if os.path.isdir('test/site'):
            shutil.copytree('test/site', output_path, dirs_exist_ok=True)
        # add packages and current plugin
        testdir = shutil.ignore_patterns('test')
        for p in packages:
            shutil.copytree(p, os.path.join(output_path,'packages/'), ignore = testdir, dirs_exist_ok=True)
        shutil.copytree('.', os.path.join(output_path,'packages/lektor-admin-utils'), ignore = testdir, dirs_exist_ok=True)
    except (OSError, IOError) as e:
        pytest.exit('FATAL: could not copy test site directory. %s', e) # error

    yield output_path

    try:
        shutil.rmtree(output_path)
    except (OSError, IOError):
        pass

class BaseUrlSession(requests.Session):
    # https://github.com/requests/toolbelt/blob/master/requests_toolbelt/sessions.py
    def __init__(self, base_url=None):
        if base_url:
            self.base_url = base_url
        super(BaseUrlSession, self).__init__()

    def request(self, method, url, *args, **kwargs):
        """Send the request after generating the complete URL."""
        url = self.create_url(url)
        return super(BaseUrlSession, self).request(
            method, url, *args, **kwargs
        )

    def create_url(self, url):
        """Create the URL based off this partial path."""
        return urljoin(self.base_url, url)


@pytest.fixture(scope='module')
def server(lektorproject, port):

    servercmd = 'lektor server -p %d'%port
    print("[START LEKTOR SERVER]")
    server = subprocess.Popen(["lektor", "server", "-p %d"%port], cwd = lektorproject)
    server.base_url = 'http://localhost:%d'%port
    time.sleep(4)
    #while True:
    #    try:
    #        requests.get(URL+'/', timeout=.2)
    #        break
    #    except requests.exceptions.Timeout:
    #        print("wait server")
    #        pass
    yield server
    print("[HALT LEKTOR SERVER]")
    server.kill()
    
def login(client, name, **kwargs):
    password = kwargs.pop('password',name)
    url = kwargs.pop('url', '/admin/root/edit')
    return client.post('/auth/login',
            data = dict( username=name, password=password, url=url),
            **kwargs)

def logout(client, **kwargs):
    return client.get('/auth/logout', **kwargs)

@pytest.fixture(scope='function')
def anonymous(server):
    session = BaseUrlSession(base_url=server.base_url)
    yield session
    session.close()

@pytest.fixture(scope='function')
def admin(server):
    session = BaseUrlSession(base_url=server.base_url)
    login(session, 'admin')
    yield session
    session.close()

@pytest.fixture(scope='function')
def blog(server):
    session = BaseUrlSession(base_url=server.base_url)
    login(session, 'blog')
    yield session
    session.close()

@pytest.fixture(scope='function')
def test(server):
    session = BaseUrlSession(base_url=server.base_url)
    login(session, 'test')
    yield session
    session.close()

@pytest.fixture(scope='module')
def project(request, lektorproject):
    from lektor.project import Project
    return Project.from_path(lektorproject)

@pytest.fixture(scope='module')
def env(request, project):
    env =  project.make_env()
    return env

@pytest.fixture(scope='function')
def pad(request, env):
    from lektor.db import Database
    return Database(env).new_pad()

@pytest.fixture(scope='module')
def webui(request, env):
    from lektor.admin.webui import WebUI
    output_path = tempfile.mkdtemp()

    def cleanup():
        try:
            shutil.rmtree(output_path)
        except (OSError, IOError):
            pass

    request.addfinalizer(cleanup)

    return WebUI(env,
            debug=True,
            output_path=output_path)

@pytest.fixture(scope='module')
def webclient(webui):
    webui.config['TESTING'] = True
    with webui.test_client() as client:
        yield client

