import pytest
import os

def test_project(lektorproject):
    print(lektorproject)
    for (dirpath, dirnames, files) in os.walk(lektorproject):
        dirnames[:] = [ d for d in dirnames if d[0] != '.' ]
        print(dirnames, files)
    assert os.path.exists(os.path.join(lektorproject,'packages/lektor-admin-utils'))

def test_server_started(anonymous):
    rv = anonymous.get('/', timeout=0.1)
    assert rv.status_code == 200

def test_auth_buttons(anonymous):
    rv = anonymous.get('/', timeout=0.1)
    assert 'auth-button-div' in rv.text

def test_static_file(anonymous):
    rv = anonymous.get('/admin-pages/static/buttons.css', timeout=0.1)
    assert 'auth-button-div' in rv.text

def test_help_page(anonymous):
    rv = anonymous.get('/admin-pages/help', timeout=0.1)
    assert '<body>' in rv.text

def test_webclient_index(webclient):
    rv = webclient.get('/')
    print(rv.data)
    assert b'<body>' in rv.data

