from mivs import *


@Session.model_mixin
class SessionMixin:
    def logged_in_studio(self):
        try:
            return self.indie_studio(cherrypy.session['studio_id'])
        except:
            raise HTTPRedirect('../mivs_applications/login')


@Session.model_mixin
class AdminAccount:
    judge = relationship('IndieJudge', uselist=False, backref='admin_account')


class IndieJudge(MagModel):
    admin_id    = Column(UUID, ForeignKey('admin_account.id'))
    genres      = Column(MultiChoice(c.INDIE_GENRE_OPTS))
    staff_notes = Column(UnicodeText)

    codes = relationship('IndieGameCode', backref='judge')
    reviews = relationship('IndieGameReview', backref='judge')

    @property
    def attendee(self):
        return self.admin_account.attendee


class IndieStudio(MagModel):
    name        = Column(UnicodeText, unique=True)
    address     = Column(UnicodeText)
    website     = Column(UnicodeText)
    twitter     = Column(UnicodeText)
    facebook    = Column(UnicodeText)
    status      = Column(Choice(c.STUDIO_STATUS_OPTS), default=c.NEW, admin_only=True)
    staff_notes = Column(UnicodeText, admin_only=True)

    games = relationship('IndieGame', backref='studio')
    developers = relationship('IndieDeveloper', backref='studio')

    @property
    def submitted_games(self):
        return [g for g in self.games if g.submitted]


class IndieDeveloper(MagModel):
    studio_id       = Column(UUID, ForeignKey('indie_studio.id'))
    primary_contact = Column(Boolean, default=False)
    first_name      = Column(UnicodeText)
    last_name       = Column(UnicodeText)
    email           = Column(UnicodeText)
    cellphone       = Column(UnicodeText)


class IndieGame(MagModel):
    studio_id         = Column(UUID, ForeignKey('indie_studio.id'))
    title             = Column(UnicodeText)
    brief_description = Column(UnicodeText)
    genres            = Column(MultiChoice(c.INDIE_GENRE_OPTS))
    description       = Column(UnicodeText)       # 500 max
    how_to_play       = Column(UnicodeText)       # 1000 max
    link_to_video     = Column(UnicodeText)
    link_to_game      = Column(UnicodeText)
    password_to_game  = Column(UnicodeText)       # web server password
    code_type         = Column(Choice(c.CODE_TYPE_OPTS), default=c.NO_CODE)
    code_instructions = Column(UnicodeText)
    build_status      = Column(Choice(c.BUILD_STATUS_OPTS))
    build_notes       = Column(UnicodeText)       # 500 max
    shown_events      = Column(UnicodeText)
    submitted         = Column(Boolean, default=False)
    agreed_liability  = Column(Boolean, default=False)
    agreed_showtimes  = Column(Boolean, default=False)
    agreed_reminder1  = Column(Boolean, default=False)
    agreed_reminder2  = Column(Boolean, default=False)
    status            = Column(Choice(c.GAME_STATUS_OPTS), default=c.NEW, admin_only=True)
    judge_notes       = Column(UnicodeText, admin_only=True)

    codes = relationship('IndieGameCode', backref='game')
    reviews = relationship('IndieGameReview', backref='game')
    screenshots = relationship('IndieGameScreenshot', backref='game')


class IndieGameScreenshot(MagModel):
    game_id     = Column(UUID, ForeignKey('indie_game.id'))
    screenshot  = Column(LargeBinary(c.MAX_SCREENSHOT_SIZE))
    description = Column(UnicodeText)


class IndieGameCode(MagModel):
    game_id     = Column(UUID, ForeignKey('indie_game.id'))
    judge_id    = Column(UUID, ForeignKey('indie_judge.id'), nullable=True)
    single_use  = Column(Boolean, default=False)
    judge_notes = Column(UnicodeText, admin_only=True)


class IndieGameReview(MagModel):
    game_id            = Column(UUID, ForeignKey('indie_game.id'))
    judge_id           = Column(UUID, ForeignKey('indie_judge.id'))
    status             = Column(Choice(c.REVIEW_STATUS_OPTS))
    score              = Column(Integer, default=0)  # 0 = not reviewed, 1-5 score (5 is best)
    feedback_developer = Column(UnicodeText)
    feedback_staff     = Column(UnicodeText)
    staff_notes        = Column(UnicodeText)
