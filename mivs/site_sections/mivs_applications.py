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
        game = session.indie_game(params, checkgroups=['genres'], bools=['agreed_liability', 'agreed_showtimes'], applicant=True)
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
        developer = session.indie_developer(params, applicant=True)
        if cherrypy.request.method == 'POST':
            message = check(developer)
            if not message:
                session.add(developer)
                raise HTTPRedirect('index?message={}', 'Presenter added')

        return {
            'message': message,
            'developer': developer
        }

    @csrf_protected
    def delete_developer(self, session, id):
        developer = session.indie_developer(id, applicant=True)
        assert not developer.primary_contact, 'You cannot delete the primary contact for a studio'
        session.delete(developer)
        raise HTTPRedirect('index?message={}', 'Presenter deleted')

    def code(self, session, game_id, message='', **params):
        code = session.indie_game_code(params, bools=['unlimited_use'], applicant=True)
        code.game = session.indie_game(game_id, applicant=True)
        if cherrypy.request.method == 'POST':
            message = check(code)
            if not message:
                session.add(code)
                raise HTTPRedirect('index?message={}', 'Code added')

        return {
            'message': message,
            'code': code
        }

    @csrf_protected
    def delete_code(self, session, id):
        code = session.indie_game_code(id, applicant=True)
        session.delete(code)
        raise HTTPRedirect('index?message={}', 'Code deleted')

    @csrf_protected
    def submit_game(self, session, id):
        game = session.indie_game(id, applicant=True)
        if not game.submittable:
            raise HTTPRedirect('index?message={}', 'You have not completed all the prerequisites for your game')
        else:
            game.submitted = True
            raise HTTPRedirect('index?message={}', 'Your game has been submitted to our panel of judges')
