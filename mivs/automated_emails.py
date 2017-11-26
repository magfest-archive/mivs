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


MIVSEmail(IndieStudio, 'Your MIVS Studio Has Been Registered', 'studio_registered.txt',
          ident='mivs_studio_registered')

MIVSEmail(IndieGame, 'Your MIVS Game Video Has Been Submitted', 'game_video_submitted.txt',
          lambda game: game.video_submitted,
          ident='mivs_video_submitted')

MIVSEmail(IndieGame, 'Your MIVS Game Has Been Submitted', 'game_submitted.txt',
          lambda game: game.submitted,
          ident='mivs_game_submitted')

MIVSEmail(IndieStudio, 'MIVS - Wat no video?', 'videoless_studio.txt',
          lambda studio: days_after(2, studio.registered)()
                     and not any(game.video_submitted for game in studio.games),
          ident='mivs_missing_video_inquiry',
          when=days_before(7, c.ROUND_ONE_DEADLINE))

MIVSEmail(IndieGame, 'MIVS: Your Submitted Video Is Broken', 'video_broken.txt',
          lambda game: game.video_broken,
          ident='mivs_video_broken')

MIVSEmail(IndieGame, 'Last chance to submit your game to MIVS', 'round_two_reminder.txt',
          lambda game: game.status == c.JUDGING and not game.submitted,
          ident='mivs_game_submission_reminder',
          when=days_before(7, c.ROUND_TWO_DEADLINE))

MIVSEmail(IndieGame, 'Your game has made it into MIVS Round Two', 'video_accepted.txt',
          lambda game: game.status == c.JUDGING,
          ident='mivs_game_made_it_to_round_two')

MIVSEmail(IndieGame, 'Your game has been declined from MIVS', 'video_declined.txt',
          lambda game: game.status == c.VIDEO_DECLINED,
          ident='mivs_video_declined')

MIVSEmail(IndieGame, 'Your game has been accepted into MIVS', 'game_accepted.txt',
          lambda game: game.status == c.ACCEPTED and not game.waitlisted,
          ident='mivs_game_accepted')

MIVSEmail(IndieGame, 'Your game has been accepted into MIVS from our waitlist', 'game_accepted_from_waitlist.txt',
          lambda game: game.status == c.ACCEPTED and game.waitlisted,
          ident='mivs_game_accepted_from_waitlist')

MIVSEmail(IndieGame, 'Your game application has been declined from MIVS', 'game_declined.txt',
          lambda game: game.status == c.GAME_DECLINED,
          ident='mivs_game_declined')

MIVSEmail(IndieGame, 'Your MIVS application has been waitlisted', 'game_waitlisted.txt',
          lambda game: game.status == c.WAITLISTED,
          ident='mivs_game_waitlisted')

MIVSEmail(IndieGame, 'Last chance to accept your MIVS booth', 'game_accept_reminder.txt',
          lambda game: game.status == c.ACCEPTED and not game.confirmed
                       and (localized_now() - timedelta(days=2)) > game.studio.confirm_deadline,
          ident='mivs_accept_booth_reminder')

MIVSEmail(IndieGame, 'MIVS December Updates: Hotels and Magfest Versus!', 'december_updates.txt',
          lambda game: game.confirmed,
          ident='mivs_december_updates')

MIVSEmail(IndieGame, 'REQUIRED: Pre-flight for MIVS due by midnight, January 2nd', 'game_preflight.txt',
          lambda game: game.confirmed,
          ident='mivs_game_preflight_reminder')

MIVSEmail(IndieGame, 'MIVS 2018: Hotel and selling signups', '2018_hotel_info.txt',
          lambda game: game.confirmed,
          ident='2018_hotel_info')


MIVSEmail(IndieGame, 'MIVS 2018: November Updates & info', '2018_email_blast.txt',
          lambda game: game.confirmed,
          ident='2018_email_blast')

MIVSEmail(IndieGame, 'Summary of judging feedback for your game', 'reviews_summary.html',
          lambda game: game.status in c.FINAL_GAME_STATUSES and game.reviews_to_email,
          ident='mivs_reviews_summary')

MIVSEmail(IndieGame, 'MIVS judging is wrapping up', 'round_two_closing.txt',
          lambda game: game.submitted, when=days_before(14, c.JUDGING_DEADLINE),
          ident='mivs_round_two_closing')

MIVSEmail(IndieJudge, 'MIVS Judging is about to begin!', 'judge_intro.txt',
          ident='mivs_judge_intro')

MIVSEmail(IndieJudge, 'MIVS Judging has begun!', 'judging_begun.txt',
          ident='mivs_judging_has_begun')

MIVSEmail(IndieJudge, 'MIVS Judging is almost over!', 'judging_reminder.txt',
          when=days_before(7, c.SOFT_JUDGING_DEADLINE),
          ident='mivs_judging_due_reminder')

MIVSEmail(IndieJudge, 'Reminder: MIVS Judging due by {}'.format(c.JUDGING_DEADLINE.strftime('%B %-d')), 'final_judging_reminder.txt',
          lambda judge: not judge.judging_complete,
          when=days_before(5, c.JUDGING_DEADLINE),
          ident='mivs_judging_due_reminder_last_chance')

MIVSEmail(IndieJudge, 'MIVS Judging and {EVENT_NAME} Staffing', 'judge_staffers.txt',
          ident='mivs_judge_staffers')

MIVSEmail(IndieJudge, 'MIVS Judge badge information', 'judge_badge_info.txt',
          ident='mivs_judge_badge_info')

MIVSEmail(IndieJudge, 'MIVS Judging about to begin', 'judge_2016.txt',
          ident='mivs_selected_to_judge')

MIVSEmail(IndieJudge, 'MIVS Judges: A Request for our MIVSY awards', '2018_mivsy_request.txt',
          ident='2018_mivsy_request')
