from mivs import *


@all_renderable()
class Root:
    def index(self, session, message=''):
        return {
            'message': message,
            'studio': session.logged_in_studio(),
        }

    def logout(self):
        cherrypy.session.pop('studio_id', None)
        raise HTTPRedirect('studio?message={}', 'You have been logged out')

    def continue_app(self, id):
        cherrypy.session['studio_id'] = id
        raise HTTPRedirect('index')

    def login(self, session, message='', studio_name=None, password=None):
        if cherrypy.request.method == 'POST':
            studio = session.query(IndieGameStudio).filter_by(name=studio_name).first()
            if not studio:
                message = 'No studio exists with that name'
            elif not studio.hashed == bcrypt.hashpw(password, studio.hashed):
                message = 'That is not the correct password'
            else:
                raise HTTPRedirect('continue_app?id={}', studio.id)

        return {'message': message}

    def studio(self, session, message='', **params):
        params.pop('id', None)
        studio = session.indie_studio(dict(params, id=cherrypy.session.get('studio_id', 'None')), restricted=True)
        developer = session.indie_developer(params)

        if cherrypy.request.method == 'POST':
            message = check(studio)
            if not message and studio.is_new:
                message = check(developer)
            if not message:
                session.add(studio)
                if studio.is_new:
                    developer.studio, developer.primary_contact = studio, True
                    session.add(developer)
                raise HTTPRedirect('continue_app?id={}', studio.id)

        return {
            'message': message,
            'studio': studio,
            'developer': developer
        }

    def game(self, session, message='', **params):
        game = session.indie_game(params, checkgroups=['genres', 'platforms'], bools=['agreed_liability', 'agreed_showtimes'], applicant=True)
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
        developer = session.indie_developer(params, applicant=True, bools=["primary_contact"])
        if cherrypy.request.method == 'POST':
            message = check(developer)
            if not message:
                primaries = session.query(IndieDeveloper).filter_by(studio_id=developer.studio_id, primary_contact=True).all()
                if not developer.primary_contact and len(primaries) == 1 and developer.id == primaries[0].id:
                    message = "Studio requires at least one presenter to receive emails."
                else:
                    session.add(developer)
                    raise HTTPRedirect('index?message={}', 'Presenters updated')

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

    def screenshot(self, session, game_id, message='', image=None, **params):
        screenshot = session.indie_game_screenshot(params, applicant=True)
        screenshot.game = session.indie_game(game_id, applicant=True)
        if cherrypy.request.method == 'POST':
            screenshot.filename = image.filename
            screenshot.content_type = image.content_type.value
            screenshot.extension = image.filename.split('.')[-1].lower()
            message = check(screenshot)
            if not message:
                with open(screenshot.filepath, 'wb') as f:
                    shutil.copyfileobj(image.file, f)
                raise HTTPRedirect('index?message={}', 'Screenshot Uploaded')

        return {
            'message': message,
            'screenshot': screenshot
        }

    def view_screenshot(self, session, id):
        screenshot = session.indie_game_screenshot(id)
        return serve_file(screenshot.filepath, name=screenshot.filename, content_type=screenshot.content_type)

    @csrf_protected
    def delete_screenshot(self, session, id):
        screenshot = session.indie_game_screenshot(id, applicant=True)
        session.delete_screenshot(screenshot)
        raise HTTPRedirect('index?message={}', 'Screenshot deleted')

    @csrf_protected
    def delete_code(self, session, id):
        code = session.indie_game_code(id, applicant=True)
        session.delete(code)
        raise HTTPRedirect('index?message={}', 'Code deleted')

    @csrf_protected
    def submit_video(self, session, id):
        game = session.indie_game(id, applicant=True)
        if not game.video_submittable:
            raise HTTPRedirect('index?message={}', 'You have not included a link to the video for your game')
        else:
            game.video_submitted = True
            raise HTTPRedirect('index?message={}', 'Your video has been submitted to our panel of judges')

    @csrf_protected
    def submit_game(self, session, id):
        game = session.indie_game(id, applicant=True)
        if not game.submittable:
            raise HTTPRedirect('index?message={}', 'You have not completed all the prerequisites for your game')
        else:
            game.submitted = True
            raise HTTPRedirect('index?message={}', 'Your game has been submitted to our panel of judges')

    def confirm(self, session, csrf_token=None, decision=None):
        studio = session.logged_in_studio()
        if not studio.comped_badges:
            raise HTTPRedirect('index?message={}', 'You did not have any games accepted')
        elif studio.group:
            raise HTTPRedirect('index?message={}', 'Your group has already been created')

        has_leader = False
        badges_remaining = studio.comped_badges
        developers = sorted(studio.developers, key=lambda d: (not d.primary_contact, d.full_name))
        for dev in developers:
            if not dev.matching_attendee and badges_remaining:
                dev.comped = True
                badges_remaining -= 1
            else:
                dev.comped = False

            if not has_leader and not getattr(dev.matching_attendee, 'group_id', None):
                dev.leader = has_leader = True
            else:
                dev.leader = False

        if cherrypy.request.method == 'POST':
            check_csrf(csrf_token)
            assert decision in ['Accept', 'Decline']
            if decision == 'Decline':
                for game in studio.games:
                    if game.status == c.ACCEPTED:
                        game.status = c.STUDIO_DECLINED
                raise HTTPRedirect('index?message={}', 'You have been marked as declining space in the showcase')
            else:
                group = studio.group = Group(name='MIVS Studio: ' + studio.name, can_add=True)
                session.add(group)
                session.commit()
                for dev in developers:
                    if dev.matching_attendee:
                        if not dev.matching_attendee.group_id:
                            group.attendees.append(dev.matching_attendee)
                            if dev.leader:
                                group.leader_id = dev.matching_attendee.id
                    else:
                        attendee = Attendee(
                            placeholder=True,
                            badge_type=c.ATTENDEE_BADGE,
                            paid=c.NEED_NOT_PAY if dev.comped else c.PAID_BY_GROUP,
                            first_name=dev.first_name,
                            last_name=dev.last_name,
                            cellphone=dev.cellphone,
                            email=dev.email
                        )
                        group.attendees.append(attendee)
                        session.commit()
                        if dev.leader:
                            group.leader_id = attendee.id
                for i in range(badges_remaining):
                    group.attendees.append(Attendee(badge_type=c.ATTENDEE_BADGE, paid=c.NEED_NOT_PAY))
                group.cost = group.default_cost
                raise HTTPRedirect('index?message={}', 'Your studio has been registered')

        return {
            'studio': studio,
            'developers': developers
        }
