from mivs import *

AutomatedEmail.queries.update({
    IndieStudio: lambda session: session.query(IndieStudio)
                                        .options(subqueryload(IndieStudio.developers),
                                                 subqueryload(IndieStudio.games)),
    IndieGame: lambda session: session.query(IndieGame)
                                      .options(joinedload(IndieGame.studio).subqueryload(IndieStudio.developers)),
    IndieJudge: lambda session: session.query(IndieJudge)
                                       .options(joinedload(IndieJudge.admin_account).joinedload(AdminAccount.attendee))
})


class MIVSEmail(AutomatedEmail):
    def __init__(self, *args, **kwargs):
        if len(args) < 4 and 'filter' not in kwargs:
            kwargs['filter'] = lambda x: True
        AutomatedEmail.__init__(self, *args, sender=c.MIVS_EMAIL, **kwargs)


MIVSEmail(IndieStudio, 'Your MIVS Studio Has Been Registered', 'studio_registered.txt')
MIVSEmail(IndieGame, 'Your MIVS Game Video Has Been Submitted', 'game_video_submitted.txt', lambda game: game.video_submitted)
MIVSEmail(IndieGame, 'Your MIVS Game Has Been Submitted', 'game_submitted.txt', lambda game: game.submitted)

MIVSEmail(IndieStudio, 'MIVS - Wat no video?', 'videoless_studio.txt',
          lambda studio: days_after(2, studio.registered)()
                     and not any(game.video_submitted for game in studio.games),
          when=days_before(7, c.ROUND_ONE_DEADLINE))

MIVSEmail(IndieGame, 'Last chance to submit your game to MIVS', 'round_two_reminder.txt',
          lambda game: game.status == c.JUDGING and not game.submitted, when=days_before(7, c.ROUND_TWO_DEADLINE))

MIVSEmail(IndieGame, 'Your game has made it into MIVS Round Two', 'video_accepted.txt',
          lambda game: game.status == c.JUDGING)

MIVSEmail(IndieGame, 'Your game has been declined from MIVS', 'video_declined.txt',
          lambda game: game.status == c.VIDEO_DECLINED)

MIVSEmail(IndieGame, 'Your game has been accepted into MIVS', 'game_accepted.txt',
          lambda game: game.status == c.ACCEPTED)

MIVSEmail(IndieGame, 'Your game application has been declined from MIVS', 'game_declined.txt',
          lambda game: game.status == c.GAME_DECLINED)

MIVSEmail(IndieGame, 'Your MIVS application has been waitlisted', 'game_waitlisted.txt',
          lambda game: game.status == c.WAITLISTED)

MIVSEmail(IndieGame, 'Last chance to accept your MIVS booth', 'game_accept_reminder.txt',
          lambda game: game.status == c.ACCEPTED and not game.confirmed, when=days_before(2, c.MIVS_CONFIRM_DEADLINE))

MIVSEmail(IndieGame, 'MIVS December Updates: Hotels and Magfest Versus!', 'december_updates.txt',
          lambda game: game.confirmed)

MIVSEmail(IndieGame, 'REQUIRED: Pre-flight for MIVS due by midnight, January 2nd', 'game_preflight.txt', lambda game: game.confirmed)

MIVSEmail(IndieGame, 'MIVS judging is wrapping up', 'round_two_closing.txt',
          lambda game: game.submitted, when=days_before(14, c.JUDGING_DEADLINE))

MIVSEmail(IndieJudge, 'MIVS Judging is about to begin!', 'judge_intro.txt')

MIVSEmail(IndieJudge, 'MIVS Judging has begun!', 'judging_begun.txt')

MIVSEmail(IndieJudge, 'MIVS Judging is almost over!', 'judging_reminder.txt',
          when=days_before(7, c.SOFT_JUDGING_DEADLINE))

MIVSEmail(IndieJudge, 'Reminder: MIVS Judging due by {}'.format(c.JUDGING_DEADLINE.strftime('%B %-d')), 'final_judging_reminder.txt',
          lambda judge: not judge.judging_complete, when=days_before(5, c.JUDGING_DEADLINE))

MIVSEmail(IndieJudge, 'MIVS Judging and {EVENT_NAME} Staffing', 'judge_staffers.txt')

MIVSEmail(IndieJudge, 'MIVS Judge badge information', 'judge_badge_info.txt')

MIVSEmail(IndieJudge, 'MIVS Judging about to begin', 'judge_2016.txt')
