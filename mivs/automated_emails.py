from mivs import *

AutomatedEmail.extra_models[IndieStudio] = lambda session: session.query(IndieStudio).all()
AutomatedEmail.extra_models[IndieGame] = lambda session: session.query(IndieGame).all()


class MIVSEmail(AutomatedEmail):
    def __init__(self, *args, **kwargs):
        AutomatedEmail.__init__(self, *args, sender=c.MIVS_EMAIL, **kwargs)


MIVSEmail(IndieStudio, 'Your MIVS Studio Has Been Registered', 'studio_registered.txt', lambda studio: True)
MIVSEmail(IndieGame, 'Your MIVS Game Video Has Been Submitted', 'game_video_submitted.txt', lambda game: game.video_submitted)
MIVSEmail(IndieGame, 'Your MIVS Game Has Been Submitted', 'game_submitted.txt', lambda game: game.submitted)
