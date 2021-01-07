# -*- coding: utf-8 -*-
from lektor.pluginsystem import Plugin
from flask import Blueprint, \
                  current_app, \
                  url_for, \
                  render_template
from lektor.admin.modules import serve, dash

utilsbp = Blueprint('utils', __name__,
                           url_prefix='/admin-pages',
                           static_folder='static',
                           template_folder='templates'
                           )

@utilsbp.route('/help')
def help():
    return render_template('help.html')

def add_content(contents, extra_routes=[]):
    """
    insert buttons in html pages

    see rewrite_html_for_editing in lektor/admin/modules/serve.py
    """
    head_endpos = contents.find(b'</head>')
    body_endpos = contents.find(b'</body>')
    if head_endpos >= 0 and body_endpos >= 0:
        # html page
        return bytes(contents[:head_endpos] +
                render_template('admin_style.html').encode('utf-8') +
                contents[head_endpos:body_endpos] +
                render_template('admin_messages.html').encode('utf-8') +
                render_template('admin_buttons.html', buttons=extra_routes).encode('utf-8') +
                contents[body_endpos:])
    # dash or iframe ?
    return bytes(contents +
            render_template('admin_style.html').encode('utf-8') +
            render_template('admin_buttons.html', buttons=extra_routes).encode('utf-8')
            )

class AdminExtraPlugin(Plugin):
    name = 'admin-extra'
    description = u'Add buttons on lektor admin pages.'
    states = ['all', 'dash' ]
    right_buttons = [ ]

    def on_setup_env(self, *args, **extra):

        @serve.bp.before_app_first_request
        def setup_blueprint():
            app = current_app
            app.register_blueprint(utilsbp)
            self.add_button( url_for('utils.help'), 'help', '?' )

        @serve.bp.after_request
        #pylint: disable=unused-variable
        def after_request_serve(response):
            if response.mimetype == "text/html":
                response.direct_passthrough = False
                response.set_data(add_content(response.get_data(),self.buttons()))
            return response

        @dash.bp.after_request
        #pylint: disable=unused-variable
        def after_request_dash(response):
            if response.mimetype == "text/html":
                response.direct_passthrough = False
                response.set_data(add_content(response.get_data(),self.buttons()))
            return response

    def add_button(self, route, title, html_entity, ignore = None):
        self.right_buttons.append( ((route, title, html_entity), ignore) )

    def buttons(self, **kwargs):
        return [ b for b,f in self.right_buttons if f is None or f(**kwargs) ]


