from mivs import *


@all_renderable(c.INDIE_JUDGE, c.INDIE_ADMIN)
class Root:
    def index(self, session):
        return {'games': session.query(IndieGame).order_by('title').all()}
