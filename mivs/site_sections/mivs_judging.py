from mivs import *


@all_renderable(c.INDIE_JUDGE)
class Root:
    def index(self, session, message=''):
        return {
            'message': message,
            'judge': session.logged_in_judge()
        }

    def studio(self, session, message='', **params):
        studio = session.indie_studio(params)
        if cherrypy.request.method == 'POST':
            # We currently only update notes, though we may add other things to this form later
            raise HTTPRedirect('index?message={}', 'Notes updated')

        return {'studio': studio}

    def video_review(self, session, message='', **params):
        review = session.indie_game_review(params)
        if cherrypy.request.method == 'POST':
            if review.video_status == c.PENDING:
                message = 'You must select a Video Status to tell us whether or not you were able to view the video'
            elif review.video_status == c.VIDEO_REVIEWED and review.video_score == c.PENDING:
                message = 'You must indicate whether or not you believe the game should pass to round 2'
            else:
                raise HTTPRedirect('index?message={}{}', review.game.title, ' video review has been uploaded')

        return {
            'message': message,
            'review': review
        }

    def game_review(self, session, message='', **params):
        review = session.indie_game_review(params, bools=['game_content_bad'])
        if cherrypy.request.method == 'POST':
            if review.game_status == c.PENDING:
                message = 'You must select a Game Status to tell us whether or not you were able to download and run the game'
            elif review.game_status == c.PLAYABLE and not review.game_score:
                message = 'You must indicate whether or not you believe the game should be accepted'
            elif review.game_status != c.PLAYABLE and review.game_score:
                message = 'If the game is not playable, please leave the score field blank'
            else:
                raise HTTPRedirect('index?message={}{}', review.game.title, ' game review has been uploaded')

        return {
            'review': review,
            'message': message,
            'game_code': session.code_for(review.game)
        }
