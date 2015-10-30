from mivs import *


@all_renderable(c.INDIE_JUDGE)
class Root:
    def index(self, session, message=''):
        return {
            'message': message,
            'judge': session.logged_in_judge()
        }

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
