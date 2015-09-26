from mivs import *


@Session.model_mixin
class SessionMixin:
    def logged_in_studio(self):
        try:
            return self.indie_studio(cherrypy.session['studio_id'])
        except:
            raise HTTPRedirect('../mivs_applications/start')

    def delete_screenshot(self, screenshot):
        self.delete(screenshot)
        try:
            os.remove(screenshot.filepath)
        except:
            pass
        self.commit()


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

    email_model_name = 'studio'

    @property
    def email(self):
        return self.primary_contact.email

    @property
    def primary_contact(self):
        return [dev for dev in self.developers if dev.primary_contact][0]

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
    password_to_game  = Column(UnicodeText)
    code_type         = Column(Choice(c.CODE_TYPE_OPTS), default=c.NO_CODE)
    code_instructions = Column(UnicodeText)
    build_status      = Column(Choice(c.BUILD_STATUS_OPTS))
    build_notes       = Column(UnicodeText)       # 500 max
    shown_events      = Column(UnicodeText)
    video_submitted   = Column(Boolean, default=False)
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

    email_model_name = 'game'

    @property
    def email(self):
        return self.studio.email

    @property
    def missing_steps(self):
        steps = []
        if not self.link_to_game:
            steps.append('You have not yet included a link to where the judges can access your game')
        if self.code_type != c.NO_CODE:
            if not self.codes:
                steps.append('You have not yet attached any codes to this game for our judges to use')
            elif not any(code.unlimited_use for code in self.codes) and len(self.codes) < c.CODES_REQUIRED:
                steps.append('You have not attached the {} codes you must provide for our judges'.format(c.CODES_REQUIRED))
        if not self.agreed_showtimes:
            steps.append('You must agree to showtimes, or something')  # TODO: figure out what this is
        if not self.agreed_liability:
            steps.append('You must check the box that agrees to our liability waiver (click the Edit link above)')
        return steps

    @property
    def video_submittable(self):
        return bool(self.link_to_video)

    @property
    def submittable(self):
        return not self.missing_steps


class IndieGameScreenshot(MagModel):
    game_id      = Column(UUID, ForeignKey('indie_game.id'))
    filename     = Column(UnicodeText)
    content_type = Column(UnicodeText)
    extension    = Column(UnicodeText)
    description  = Column(UnicodeText)

    @property
    def url(self):
        return '../mivs_applications/view_screenshot?id={}'.format(self.id)

    @property
    def filepath(self):
        return os.path.join(c.SCREENSHOT_DIR, str(self.id))


class IndieGameCode(MagModel):
    game_id       = Column(UUID, ForeignKey('indie_game.id'))
    judge_id      = Column(UUID, ForeignKey('indie_judge.id'), nullable=True)
    code          = Column(UnicodeText)
    unlimited_use = Column(Boolean, default=False)
    judge_notes   = Column(UnicodeText, admin_only=True)

    @property
    def type_label(self):
        return 'Unlimited-Use' if self.unlimited_use else 'Single-Person'


class IndieGameReview(MagModel):
    game_id            = Column(UUID, ForeignKey('indie_game.id'))
    judge_id           = Column(UUID, ForeignKey('indie_judge.id'))
    status             = Column(Choice(c.REVIEW_STATUS_OPTS))
    score              = Column(Integer, default=0)  # 0 = not reviewed, 1-5 score (5 is best)
    feedback_developer = Column(UnicodeText)
    feedback_staff     = Column(UnicodeText)
    staff_notes        = Column(UnicodeText)


@on_startup
def add_applicant_restriction():
    """
    We use convenience functions for our form handling, e.g. to instantiate an
    attendee from an id or from form data we use the session.attendee() method.
    This method runs on startup and overrides the methods which are used for the
    game application forms to add a new "applicant" parameter.  If truthy, this
    triggers three additional behaviors:
    1) We check that there is currently a logged in studio, and redirect to the
       login page if there is not.
    2) We check that the item being edited belongs to the currently-logged-in
       studio and raise an exception if it does not.  This check is bypassed for
       new things which have not yet been saved to the database.
    3) If the model is one with a "studio" relationship, we set that to the
       currently-logged-in studio.
    """
    def override_getter(method_name):
        orig_getter = getattr(Session.SessionMixin, method_name)

        @wraps(orig_getter)
        def with_applicant(self, *args, **kwargs):
            applicant = kwargs.pop('applicant', False)
            instance = orig_getter(self, *args, **kwargs)
            if applicant:
                studio = self.logged_in_studio()
                if hasattr(instance.__class__, 'game'):
                    assert instance.is_new or studio == instance.game.studio
                else:
                    assert instance.is_new or studio == instance.studio
                    instance.studio = studio
            return instance
        setattr(Session.SessionMixin, method_name, with_applicant)

    for name in ['indie_developer', 'indie_game', 'indie_game_code', 'indie_game_screenshot']:
        override_getter(name)
