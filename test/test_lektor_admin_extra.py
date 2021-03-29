import pytest
import os

def test_project(lektorproject):
    print(lektorproject)
    for (dirpath, dirnames, files) in os.walk(lektorproject):
        #dirnames[:] = [ d for d in dirnames if d[0] != '.' ]
        dirnames[:] = [ d for d in dirnames if d[0] != '.' ]
        print(dirnames, files)
    assert os.path.exists(os.path.join(lektorproject,'packages/lektor-admin-utils'))

def test_webclient_index(webclient):
    rv = webclient.get('/')
    print(rv.data)
    assert b'<body>' in rv.data

def test_webclient_buttons(webclient):
    rv = webclient.get('/')
    assert b'auth-button-div' in rv.data

# no test for plugin.bp.route, impossible to
# add route dynamically

def test_webclient_add_button(env, webclient):
    from lektor.pluginsystem import get_plugin
    plugin = get_plugin('admin-extra', env)
    plugin.add_button('/', 'zorglub', 'H')

    rv = webclient.get('/')
    assert b'zorglub' in rv.data

    rv = webclient.get('/blog')
    assert b'zorglub' in rv.data

    rv = webclient.get('/admin/edit')
    assert b'zorglub' in rv.data

def test_webclient_add_serve_button(env, webclient):
    from lektor.pluginsystem import get_plugin
    plugin = get_plugin('admin-extra', env)
    plugin.add_serve_button('/nirvana', 'albatros', 'A')

    rv = webclient.get('/')
    print(rv.data)
    assert b'albatros' in rv.data

    rv = webclient.get('/admin/edit')
    print(rv.data)
    assert b'albatros' not in rv.data

def test_webclient_add_dash_button(env, webclient):
    from lektor.pluginsystem import get_plugin
    plugin = get_plugin('admin-extra', env)

    plugin.add_dash_button('/devnull', 'Rnd0m', 'F')

    rv = webclient.get('/')
    print(rv.data)
    assert b'Rnd0m' not in rv.data

    rv = webclient.get('/admin/edit')
    print(rv.data)
    assert b'Rnd0m' in rv.data

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
    assert 'Aide' in rv.text

