import colander

import deform.widget

from pyramid.httpexceptions import HTTPFound
from .resources import DBSession, Page, Users

import hashlib
from pyramid.httpexceptions import HTTPFound
from pyramid.security import (
    remember,
    forget,
    authenticated_userid
    )

from pyramid.view import (
    view_config,
    view_defaults,
    forbidden_view_config
    )

#from .security import USERS
class DataPage(colander.MappingSchema):
    title = colander.SchemaNode(colander.String())
    body = colander.SchemaNode(
        colander.String() )

class UserPage(colander.MappingSchema):
    choices = (
            ('', '- Select -'),
            ('some', 'Some'),
            ('admin', 'Admin'),
            ('viewer', 'Visitor')
            )
    username = colander.SchemaNode(colander.String())
    password = colander.SchemaNode(colander.String(),widget=deform.widget.PasswordWidget(size=20) )
    group = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.SelectWidget(values=choices)
                )
#    group = colander.SchemaNode(
#                colander.String(),
#                default='some', # <--- raison d'etre
#                validator=colander.OneOf(['some', 'admin']),
#                widget=deform.widget.SelectWidget(values=choices))
#                title='Pepper Chooser',
#                description='Select a Pepper')
    

class DataViews(object):
    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid

    @property
    def data_form(self):
        schema = DataPage()
        return deform.Form(schema, buttons=('submit',))

    @property
    def user_form(self):
        schema = UserPage()
        return deform.Form(schema, buttons=('submit',))

    @property
    def reqts(self):
        return self.data_form.get_widget_resources()

    @view_config(route_name='data_view', renderer='data_view.pt', permission='edit')
    def data_view(self):
        request = self.request
        pages = DBSession.query(Page).order_by(Page.title).filter(request.authenticated_userid == Page.username)
        return dict(title='Data View', pages=pages)

    @view_config(route_name='datapage_add',
                 renderer='datapage_addedit.pt', permission='edit')
    def datapage_add(self):
        form = self.data_form.render()

        if 'submit' in self.request.params:
            controls = self.request.POST.items()
            try:

                appstruct = self.data_form.validate(controls)
            except deform.ValidationFailure as e:
                # Form is NOT valid
                return dict(form=e.render())
            request=self.request  
            # Add a new page to the database
            new_title = appstruct['title']
            new_body = appstruct['body']
            DBSession.add(Page(title=new_title, body=new_body,username=request.authenticated_userid))

            # Get the new ID and redirect
            page = DBSession.query(Page).filter_by(title=new_title).one()
            new_uid = page.uid

            url = self.request.route_url('datapage_view', uid=new_uid)
            return HTTPFound(url)

        return dict(form=form)


    @view_config(route_name='datapage_view', renderer='datapage_view.pt', permission='edit')
    def datapage_view(self):
        uid = int(self.request.matchdict['uid'])
        page = DBSession.query(Page).filter_by(uid=uid).one()
        return dict(page=page)


    @view_config(route_name='datapage_edit',
                 renderer='datapage_addedit.pt', permission='edit')
    def datapage_edit(self):
        uid = int(self.request.matchdict['uid'])
        page = DBSession.query(Page).filter_by(uid=uid).one()

        data_form = self.data_form

        if 'submit' in self.request.params:
            controls = self.request.POST.items()
            try:
                appstruct = data_form.validate(controls)
            except deform.ValidationFailure as e:
                return dict(page=page, form=e.render())

            # Change the content and redirect to the view
            page.title = appstruct['title']
            page.body = appstruct['body']
            url = self.request.route_url('datapage_view', uid=uid)
            return HTTPFound(url)

        form = self.data_form.render(dict(
            uid=page.uid, title=page.title, body=page.body)
        )

        return dict(page=page, form=form)
    @view_config(route_name='datapage_delete', permission='edit')
    def datapage_delete(self):
        uid = int(self.request.matchdict['uid'])
        page = DBSession.query(Page).filter_by(uid=uid).one()
        DBSession.delete(page)

        url = self.request.route_url('data_view')
        return HTTPFound(url)

    @view_config(route_name='login', renderer='login.pt')
    @forbidden_view_config(renderer='login.pt')
    def login(self):
        request = self.request
        login_url = request.route_url('login')
        referrer = request.url
        if referrer == login_url:
            referrer = '/'  # never use login form itself as came_from
        came_from = request.params.get('came_from', referrer)
        message = ''
        login = ''
        password = ''
        if 'form.submitted' in request.params:
            session = DBSession
            login = request.params['login']
            password = request.params['password']
            user = session.query(Users).filter(Users.username==login).filter(Users.password ==password).count()
            if(user != 0):
                headers = remember(request, login)
                return HTTPFound(location=came_from,headers=headers)
            else:
                message = 'Failed login'

        return dict(
            name='Login',
            message=message,
            url=request.application_url + '/login',
            came_from=came_from,
            login=login,
            password=password,
        )
    @view_config(route_name='home', renderer='home.pt')
    def home(self):
        pages = DBSession.query(Page).order_by(Page.title)
        return dict(title='Welcome', pages=pages)

    @view_config(route_name='logout')
    def logout(self):
        request = self.request
        headers = forget(request)
        url = request.route_url('home')
        return HTTPFound(location=url,
                         headers=headers)
    @view_config(route_name='user_add',
                 renderer='user_addedit.pt', permission='admin')
    def user_add(self):
        form = self.user_form.render()

        if 'submit' in self.request.params:
            controls = self.request.POST.items()
            try:
                appstruct = self.user_form.validate(controls)
            except deform.ValidationFailure as e:
                # Form is NOT valid
                return dict(form=e.render())

            # Add a new page to the database
            new_username = appstruct['username']
            new_password = appstruct['password']
            new_group = appstruct['group']
            DBSession.add(Users(username=new_username, password=new_password,group=new_group))

            url = self.request.route_url('adminpage')
            return HTTPFound(url)

        return dict(form=form)
    @view_config(route_name='adminpage', renderer='adminpage.pt')
    def adminpage(self):
        pages = DBSession.query(Page).order_by(Page.title)
        return dict(title='Admin', pages=pages) 
