from mivs import *


@all_renderable(c.INDIE_ADMIN)
class Root:
    def index(self, session, message=''):
        return {
            'message': message,
            'judges': session.indie_judges(),
            'games': [g for g in session.indie_games() if g.video_submitted]
        }

    @csv_file
    def everything(self, out, session):
        out.writerow([
            'Game', 'Studio', 'Primary Contact Name', 'Primary Contact Email',
            'Genres', 'Brief Description', 'Long Description', 'How to Play',
            'Link to Video', 'Link to Game', 'Game Link Password',
            'Game Requires Codes?', 'Code Instructions', 'Build Status', 'Build Notes',
            'Video Submitted', 'Game Submitted', 'Current Status', 'Registered',
            'Average Score', 'Individual Scores'
        ])
        for game in session.indie_games():
            out.writerow([
                game.title,
                game.studio.name,
                game.studio.primary_contact.full_name,
                game.email,
                ' / '.join(game.genres_labels),
                game.brief_description,
                game.description,
                game.how_to_play,
                game.link_to_video,
                game.link_to_game,
                game.password_to_game,
                game.code_type_label,
                game.code_instructions,
                game.build_status_label,
                game.build_notes,
                'submitted' if game.video_submitted else 'not submitted',
                'submitted' if game.submitted else 'not submitted',
                game.status_label,
                game.registered.strftime('%Y-%m-%d'),
                str(game.average_score)
            ] + [str(score) for score in game.scores])

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
        game_id, judge_id = listify(game_id), listify(judge_id)
        for gid in listify(game_id):
            for jid in listify(judge_id):
                if not session.query(IndieGameReview).filter_by(game_id=gid, judge_id=jid).first():
                    session.add(IndieGameReview(game_id=gid, judge_id=jid))
        raise HTTPRedirect(return_to, 'Assignment successful')

    def video_results(self, session, id):
        return {'game': session.indie_game(id)}

    def game_results(self, session, id):
        return {'game': session.indie_game(id)}

    @csrf_protected
    def mark_verdict(self, session, id, status):
        if not status:
            raise HTTPRedirect('index?message={}', 'You did not mark a status')
        else:
            game = session.indie_game(id)
            game.status = int(status)
            raise HTTPRedirect('index?message={}{}{}', game.title, ' has been marked as ', game.status_label)

    def problems(self, session, game_id):
        game = session.indie_game(game_id)
        if not game.has_issues:
            raise HTTPRedirect('index?message={}{}', game.title, ' has no outstanding issues')
        else:
            return {'game': game}

    @csrf_protected
    def reset_problems(self, session, game_id):
        game = session.indie_game(game_id)
        for review in game.reviews:
            if review.has_video_issues:
                review.video_status = c.PENDING
            if review.has_game_issues:
                review.game_status = c.PENDING
        raise HTTPRedirect('index?message={}{}', review.game.title, ' has been marked as having its judging issues fixed')
