from .resources import (
    DBSession,
    Users,
    )

def groupfinder(userid, request): 
    session = DBSession()
    for instance in session.query(Users).filter(Users.username==userid):
        group = 'group:'+instance.group 
        lsth = {'userid':[group]}
        return lsth.get  ('userid')   
