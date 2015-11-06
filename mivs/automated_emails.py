from mivs import *

AutomatedEmail.extra_models[IndieStudio] = lambda session: session.query(IndieStudio).all()
AutomatedEmail.extra_models[IndieGame] = lambda session: session.query(IndieGame).all()


class MIVSEmail(AutomatedEmail):
    def __init__(self, *args, **kwargs):
        AutomatedEmail.__init__(self, *args, sender=c.MIVS_EMAIL, **kwargs)


MIVSEmail(IndieStudio, 'Your MIVS Studio Has Been Registered', 'studio_registered.txt', lambda studio: True)
MIVSEmail(IndieGame, 'Your MIVS Game Video Has Been Submitted', 'game_video_submitted.txt', lambda game: game.video_submitted)
MIVSEmail(IndieGame, 'Your MIVS Game Has Been Submitted', 'game_submitted.txt', lambda game: game.submitted)

MIVSEmail(IndieStudio, 'MIVS - Wat no video?', 'videoless_studio.txt',
          lambda studio: days_after(2, studio.registered)
                     and days_before(7, c.ROUND_ONE_DEADLINE)
                     and not any([g.link_to_video for g in studio.games]))

MIVSEmail(IndieGame, 'Your game has made it into MIVS Round Two', 'video_accepted.txt',
          lambda game: game.status == c.JUDGING)

MIVSEmail(IndieGame, 'Your game has been declined from MIVS', 'video_declined.txt',
          lambda game: game.status == c.VIDEO_DECLINED)
