from mivs import *


@all_renderable(c.INDIE_ADMIN)
class Root:
    def index(self, session, message=''):
        return {
            'message': message,
            'judges': session.indie_judges(),
            'games': [g for g in session.indie_games() if g.video_submitted]
        }

    def create_judge(self, session, message='', first_name='', last_name='', email='', **params):
        judge = session.indie_judge(params, checkgroups=['genres'])
        if cherrypy.request.method == 'POST':
            message = check(judge)
            if not message and not first_name or not last_name or not email:
                message = 'First name, last name, and email address are all required to add a judge'

            if not message:
                # only match on last name and email, to prevent nickname issues; this could cause
                # problems if we had two judges with the same last name AND the same email address
                attendee = session.query(Attendee).filter_by(last_name=last_name, email=email).first()
                if attendee and attendee.admin_account:
                    if attendee.admin_account.judge:
                        raise HTTPRedirect('index?message={}{}', attendee.full_name, ' is already registered as a judge')
                    else:
                        attendee.admin_account.judge = judge
                        attendee.admin_account.access = ','.join(map(str, set(attendee.admin_account.access_ints + [c.INDIE_JUDGE])))
                        raise HTTPRedirect('index?message={}{}', attendee.full_name, ' has been granted judge access')

                if not attendee:
                    attendee = Attendee(first_name=first_name, last_name=last_name, email=email,
                                        placeholder=True, badge_type=c.STAFF_BADGE, paid=c.NEED_NOT_PAY)
                    session.add(attendee)

                password = genpasswd()
                attendee.admin_account = AdminAccount(
                    judge=judge,
                    access=str(c.INDIE_JUDGE),
                    hashed=bcrypt.hashpw(password, bcrypt.gensalt())
                )
                email_body = render('emails/accounts/new_account.txt', {
                    'password': password,
                    'account': attendee.admin_account
                })
                send_email(c.MIVS_EMAIL, attendee.email, 'New ' + c.EVENT_NAME + ' Ubersystem Account', email_body)
                raise HTTPRedirect('index?message={}{}', attendee.full_name, ' has been given an admin account as an Indie Judge')

        return {
            'message': message,
            'judge': judge,
            'first_name': first_name,
            'last_name': last_name,
            'email': email
        }

    def edit_judge(self, session, message='', **params):
        judge = session.indie_judge(params)
        if cherrypy.request.method == 'POST':
            message = check(judge)
            if not message:
                raise HTTPRedirect('index?message={}', 'Judge info updated')

        return {
            'judge': judge,
            'message': message
        }

    def assign_games(self, session, judge_id, message=''):
        judge = session.indie_judge(judge_id)
        unassigned_games = [g for g in session.indie_games() if g.video_submitted and judge.id not in (r.judge_id for r in g.reviews)]
        if judge.all_genres:
            matching, nonmatching = unassigned_games, []
        else:
            matching = [g for g in unassigned_games if set(judge.genres_ints).intersection(g.genres_ints)]
            nonmatching = [g for g in unassigned_games if g not in matching]

        return {
            'judge': judge,
            'message': message,
            'matching': matching,
            'nonmatching': nonmatching
        }

    def assign_judges(self, session, game_id, message=''):
        game = session.indie_game(game_id)
        unassigned_judges = [j for j in session.indie_judges() if j.id not in (r.judge_id for r in game.reviews)]
        matching = [j for j in unassigned_judges if j.all_genres or set(game.genres_ints).intersection(j.genres_ints)]
        nonmatching = [j for j in unassigned_judges if j not in matching]
        return {
            'game': game,
            'message': message,
            'matching': matching,
            'nonmatching': nonmatching
        }

    @csrf_protected
    def assign(self, session, game_id, judge_id, return_to):
        return_to = return_to + '&message={}'
        if session.query(IndieGameReview).filter_by(game_id=game_id, judge_id=judge_id).first():
            raise HTTPRedirect(return_to, 'That game has already been assigned to that judge')
        else:
            session.add(IndieGameReview(game_id=game_id, judge_id=judge_id))
            raise HTTPRedirect(return_to, 'Game assigned to judge')
