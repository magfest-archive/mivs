from mivs import *


@all_renderable()
class Root:
    def index(self, session, message=''):
        return {
            'message': message,
            'studio': session.logged_in_studio()
        }

    def login(self):
        return {}

    def continue_app(self, id):
        cherrypy.session['studio_id'] = id
        raise HTTPRedirect('index')

    def studio(self, session, message='', **params):
        params.pop('id', None)
        studio = session.indie_studio(dict(params, id=cherrypy.session.get('studio_id', 'None')), restricted=True)
        developer = session.indie_developer(params)
        developer.studio, developer.primary_contact = studio, True

        if cherrypy.request.method == 'POST':
            message = check(studio)
            if not message and studio.is_new:
                message = check(developer)
            if not message:
                session.add(studio)
                if studio.is_new:
                    session.add(developer)
                raise HTTPRedirect('continue_app?id={}', studio.id)

        return {
            'message': message,
            'studio': studio,
            'developer': developer
        }

    def game(self, session, message='', **params):
        studio = session.logged_in_studio()
        game = session.indie_game(params, checkgroups=['genres'], bools=['agreed_liability', 'agreed_showtimes'])
        assert game.is_new or game.studio == studio, 'No hacking allowed!'
        game.studio = studio

        if cherrypy.request.method == 'POST':
            message = check(game)
            if not message:
                session.add(game)
                raise HTTPRedirect('index?message={}', 'Game information uploaded')

        return {
            'game': game,
            'message': message
        }

    def developer(self, session, message='', **params):
        studio = session.logged_in_studio()
        developer = session.indie_developer(params)
        assert developer.is_new or developer.studio == studio, 'No hacking allowed!'
        developer.studio = studio

        if cherrypy.request.method == 'POST':
            message = check(developer)
            if not message:
                session.add(developer)
                raise HTTPRedirect('index?message={}', 'Presenter added')

        return {
            'message': message,
            'developer': developer
        }

    def delete_developer(self, session, id):
        studio = session.logged_in_studio()
        developer = session.indie_developer(id)
        assert developer.studio == studio, 'No hacking allowed!'
        session.delete(developer)
        raise HTTPRedirect('index?message={}', 'Presenter deleted')
