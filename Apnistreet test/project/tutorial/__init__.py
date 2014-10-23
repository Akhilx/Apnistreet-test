from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator

from .security import groupfinder

from sqlalchemy import engine_from_config

from .resources import DBSession, Base

def main(global_config, **settings):
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

    config = Configurator(settings=settings,
                          root_factory='.resources.Root')
    config.include('pyramid_chameleon')

    # Security policies
    authn_policy = AuthTktAuthenticationPolicy(
        settings['tutorial.secret'], callback=groupfinder,
        hashalg='sha512')
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('home','/')
    config.add_route('user_add','/admin')
    config.add_route('adminpage', '/admin/view')
    config.add_route('data_view', '/view')
    config.add_route('datapage_add', '/add')
    config.add_route('datapage_view', '/{uid}')
    config.add_route('datapage_edit', '/{uid}/edit')
    config.add_route('datapage_delete', '/{uid}/del')
    config.add_static_view('deform_static', 'deform:static/')
    config.scan('.views')
    return config.make_wsgi_app()
