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
    parser.addoption("--project", action="store")
    parser.addini('project', 'path or git repo of the lektor test project')
    parser.addoption("--branch", action="append")
    parser.addini('branch', 'git branches to checkout', 'linelist', default=['master'])
    parser.addoption("--package", action="append")
    parser.addini('packages', 'plugins path to add', 'linelist') # dunno how pathlist is parsed
    parser.addoption("--port", action="store")
    parser.addini('port', 'http server port', default='5787')

def get_config(config, name):
    v = config.getoption(name)
    if v is None:
        v = config.getini(name)
    print(name, v)
    return v

@pytest.fixture(scope='session')
def project_path(request):
    """
    Warning: do not put .git after github repo
    pytest --project='https://github.com/pascalmolin/lektor-test-site'
    instead of
    pytest --project='https://github.com/pascalmolin/lektor-test-site.git'
    """
    return get_config(request.config, 'project')

@pytest.fixture(scope='session')
def port(request):
    return int(request.config.getini('port'))

@pytest.fixture(scope='session')
def packages(request):
    return request.config.getini('packages')

def git_clone(project_path, output_path, branchname='master'):
    subprocess.run(
        ["git", "clone",
            "--single-branch", "--branch", branchname,
            "--recurse-submodules",
            project_path ],
        check=True,
        cwd = output_path
    )

def pytest_generate_tests(metafunc):
    branches = get_config(metafunc.config,'branch')
    if 'branchname' in metafunc.fixturenames:
        metafunc.parametrize("branchname", branches, scope='session')

@pytest.fixture(scope='session')
def lektorproject(project_path, branchname, packages):

    output_path = tempfile.mkdtemp()
    print('OUT: ', output_path)

    # copy main repo
    print('CLONE %s to %s'%(project_path, output_path))
    git_clone(project_path, output_path, branchname)
    name = os.path.basename(os.path.normpath(project_path))
    output_path = os.path.join(output_path, name)
    packages_path = os.path.join(output_path,'packages')
    os.mkdir(packages_path)
    for p in packages + [ os.getcwd() ]:
        print('CLONE package %s to %s'%(p,packages_path))
        p = os.path.normpath(p)
        git_clone(p, packages_path)
    print('OUTPUT PATH = %s'%output_path)

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
    time.sleep(5)
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
def view(server):
    session = BaseUrlSession(base_url=server.base_url)
    login(session, 'view')
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
def draft(server):
    session = BaseUrlSession(base_url=server.base_url)
    login(session, 'draft')
    yield session
    session.close()

### API

@pytest.fixture(scope='module')
def project(lektorproject, branchname):
    if branchname != 'lektor-admin-extra':
        pytest.skip('already tested')
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

    yield WebUI(env,
            debug=True,
            output_path=output_path)
    try:
        shutil.rmtree(output_path)
    except (OSError, IOError):
        pass


@pytest.fixture(scope='module')
def webclient(webui):
    webui.config['TESTING'] = True
    print('Starting up client')
    with webui.test_client() as client:
        yield client
    print('Shutting down client')
