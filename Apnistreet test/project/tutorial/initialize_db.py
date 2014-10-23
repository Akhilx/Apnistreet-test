import os
import sys
import transaction

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from .resources import (
    DBSession,
    Page,
    Users,
    Base,
    )


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    with transaction.manager:
        model = Page(title='Root', body='<p>Root</p>', username='admin')
        DBSession.add(model)
        model = Page(title='Run', body='Run', username='rawal')
        DBSession.add(model)
        model = Users(username='admin', password='admin123',group='admin')
        DBSession.add(model)
        model = Users(username='raw', password='akhilesh',group='admin')
        DBSession.add(model)
        model = Users(username='rawal', password='akhilesh',group='some')
        DBSession.add(model)

