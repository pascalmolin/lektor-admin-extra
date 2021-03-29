# admin-extra

Add facilities for the lektor development server.

## Help pages

By default, a ``?`` help button is added to all served pages,
which links to a main help page.

If the lektor project contains a ``content/admin-pages`` folder,
the help button will redirect there. This page should have system
fields ``_hidden: yes`` and ``_discoverable: no``.

If ``content/admin-pages`` is not found, the default
``template/help.html`` of this plugin is served instead.

When writing ``admin-pages``, consider extending the default
``template/help.html``.

Add extra buttons and messages to lektor admin panel.

## Adding custom buttons

Besides the default ``?`` help button, the plugin makes it possible
to register other links. For example, the ``lektor-login``
plugin registers a logout link.

Use ``add_serve_button(url, tooltip, html)`` to add a button
to all served pages, and ``add_dash_button`` for dash.

Example
```
class MyPlugin(Plugin):
    def on_setup_env(self, *args, **extra):
        admin_extra = get_plugin('admin-extra', self.env)
        admin_extra.add_button( '/secret/url', 'hidden diary', ':-/' )
```

Trick: in order to use ``url_for``, the code must run after Flask app has
started. An option is to register under ``before_app_first_request``
```
        from lektor.admin.modules import serve
        @serve.bp.before_app_first_request
        def register_button():
            admin_extra.add_button( '/secret/url', 'hidden diary', ':-/' )
```

## Adding help pages

All 
