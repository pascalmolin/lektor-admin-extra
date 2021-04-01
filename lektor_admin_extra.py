# -*- coding: utf-8 -*-
from flask import Blueprint, \
                  current_app, \
                  url_for, \
                  render_template
from lektor.pluginsystem import Plugin
from lektor.admin.modules import serve, dash

utilsbp = Blueprint('admin_utils', __name__,
                           url_prefix='/admin-pages',
                           static_folder='static',
                           template_folder='templates'
                           )

def add_content(contents, extra_routes=None):
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
    right_buttons = { 'serve' : [], 'dash': [] }
    help_data = {
            'index': []
            }
    help_dir = None
    bp = utilsbp

    def emit(self, event, **kwargs):
        """ lektor bug, now fixed #859 """
        return self.env.plugin_controller.emit(self.id + "-" + event, **kwargs)

    #pylint: disable=unused-variable
    def on_setup_env(self, *args, **extra):
        """
        initialize routes and buttons
        top help page redirects to the directory
        under self.get_config().get('help_pages')
        (which default to /admin-pages)
        or a default help page.
        """

        self.parse_config()


        @serve.bp.before_app_first_request
        def setup_blueprint():
            app = current_app
            app.register_blueprint(utilsbp)
            # only if no help pages defined
            if self.help_dir is not None:
                self.add_button(self.help_dir, 'help', '?', index=0 )
            else:
                self.add_button( url_for('admin_utils.help'), 'help', '?', index=0 )

        @serve.bp.after_request
        #pylint: disable=unused-variable
        def after_request_serve(response):
            if response.mimetype == "text/html":
                response.direct_passthrough = False
                response.set_data(add_content(response.get_data(),self.buttons('serve')))
            return response

        @dash.bp.after_request
        #pylint: disable=unused-variable
        def after_request_dash(response):
            if response.mimetype == "text/html":
                response.direct_passthrough = False
                response.set_data(add_content(response.get_data(),self.buttons('dash')))
            return response

        @utilsbp.route('/help')
        #pylint: disable=unused-variable
        def help():
            pad = self.env.new_pad()
            return render_template('help.html', this=self.help_data, site=pad, help_root=self.help_dir)
            #return self.env.render_template('help.html', this=self.help_data)

    def buttons(self, bp, **kwargs):
        return [ b for b,f in self.right_buttons[bp] if f is None or f(**kwargs) ]

    def add_button(self, route, title, html_entity, bp=['serve','dash'], ignore=None, index=None):
        print("register button %s -> %s"%(title, route))
        for b in bp:
            if index is None or index > len(self.right_buttons[b]):
                self.right_buttons[b].append( ((route, title, html_entity), ignore) )
            else:
                self.right_buttons[b].insert(index, ((route, title, html_entity), ignore) )
    def add_serve_button(self, *args, **kwargs):
        self.add_button(*args, bp=['serve'], **kwargs)
    def add_dash_button(self, *args, **kwargs):
        self.add_button(*args, bp=['dash'], **kwargs)
    def add_help_page(self, url, item):
        self.help_data['index'].append( (url, item) )

    def parse_config(self):
        """ register buttons defined in configs/admin-extra.ini """
        config = self.get_config()
        self.help_dir = config.get('help_pages', None)
        prefix = 'button.'
        button_names = [ s[len(prefix):] for s in config.sections() if s[:len(prefix)] == prefix ]
        for name in button_names:
            print(name)
            get = lambda k: config.get(prefix+name+'.'+k,None)
            (url, html, title, index) = map(get, ['url','html','title', 'index'])
            scope = ['serve','dash']
            if get('scope'):
                scope = [s for s in get('scope').split(',') if s in ['serve','dash']]
            self.add_button(url, title, html, bp=scope, index=index)


