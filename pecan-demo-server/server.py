import pecan
from werkzeug import serving


def get_pecan_config():
    # Set up the pecan configuration
    return pecan.configuration.conf_from_file('config.py')


def setup_app(extra_hooks=None):
    # FIXME: Replace DBHook with a hooks.TransactionHook
    app_hooks = [
        # hooks.ConfigHook(),
        # hooks.DBHook(),
        # hooks.TranslationHook(),
        # hooks.ThreadLockHook(),
        # hooks.LogHook()
    ]
    if extra_hooks:
        app_hooks.extend(extra_hooks)

    pecan_config = pecan.configuration.conf_from_file('config.py')

    pecan.configuration.set_config(dict(pecan_config), overwrite=True)

    # NOTE(sileht): pecan debug won't work in multi-process environment
    pecan_debug = False

    app = pecan.make_app(
        pecan_config.app.root,
        debug=pecan_debug,
        force_canonical=getattr(pecan_config.app, 'force_canonical', False),
        # hooks=app_hooks,
        # wrap_app=middleware.ParsableErrorMiddleware,
        guess_content_type_from_ext=False
    )

    return app


serving.run_simple('0.0.0.0', 55127,
                   setup_app(), threaded=True, processes=1)
