from mivs import *


def href(url):
    return ('http://' + url) if url and not url.startswith('http') else url


class ReviewMixin:
    @property
    def video_reviews(self):
        return [r for r in self.reviews if r.video_status != c.PENDING]

    @property
    def game_reviews(self):
        return [r for r in self.reviews if r.game_status != c.PENDING]


@Session.model_mixin
class SessionMixin:
    def logged_in_studio(self):
        try:
            return self.indie_studio(cherrypy.session['studio_id'])
        except:
            raise HTTPRedirect('../mivs_applications/studio')

    def logged_in_judge(self):
        judge = self.admin_attendee().admin_account.judge
        if judge:
            return judge
        else:
            raise HTTPRedirect('../accounts/homepage?message={}', 'You have been given judge access but not had a judge entry created for you - please contact a MIVS admin to correct this.')

    def code_for(self, game):
        if game.unlimited_code:
            return game.unlimited_code
        else:
            for code in self.logged_in_judge().codes:
                if code.game == game:
                    return code

    def delete_screenshot(self, screenshot):
        self.delete(screenshot)
        try:
            os.remove(screenshot.filepath)
        except:
            pass
        self.commit()

    def indie_judges(self):
        return self.query(IndieJudge).join(IndieJudge.admin_account).join(AdminAccount.attendee).order_by(Attendee.full_name).all()

    def indie_games(self):
        return self.query(IndieGame).options(joinedload(IndieGame.studio), joinedload(IndieGame.reviews)).order_by('name').all()


@Session.model_mixin
class AdminAccount:
    judge = relationship('IndieJudge', uselist=False, backref='admin_account')


@Session.model_mixin
class Group:
    studio = relationship('IndieStudio', uselist=False, backref='group')


class IndieJudge(MagModel, ReviewMixin):
    admin_id    = Column(UUID, ForeignKey('admin_account.id'))
    genres      = Column(MultiChoice(c.INDIE_JUDGE_GENRE_OPTS))
    platforms   = Column(MultiChoice(c.INDIE_PLATFORM_OPTS))
    platforms_text = Column(UnicodeText)
    staff_notes = Column(UnicodeText)

    codes = relationship('IndieGameCode', backref='judge')
    reviews = relationship('IndieGameReview', backref='judge')

    email_model_name = 'judge'

    @property
    def judging_complete(self):
        return len(self.reviews) == len(self.game_reviews)

    @property
    def all_genres(self):
        return c.ALL_GENRES in self.genres_ints

    @property
    def attendee(self):
        return self.admin_account.attendee

    @property
    def full_name(self):
        return self.attendee.full_name

    @property
    def email(self):
        return self.attendee.email


class IndieStudio(MagModel):
    group_id    = Column(UUID, ForeignKey('group.id'), nullable=True)
    name        = Column(UnicodeText, unique=True)
    address     = Column(UnicodeText)
    website     = Column(UnicodeText)
    twitter     = Column(UnicodeText)
    facebook    = Column(UnicodeText)
    status      = Column(Choice(c.STUDIO_STATUS_OPTS), default=c.NEW, admin_only=True)
    staff_notes = Column(UnicodeText, admin_only=True)
    registered  = Column(UTCDateTime, server_default=utcnow())

    games = relationship('IndieGame', backref='studio', order_by='IndieGame.title')
    developers = relationship('IndieDeveloper', backref='studio', order_by='IndieDeveloper.last_name')

    email_model_name = 'studio'

    @property
    def website_href(self):
        return href(self.website)

    @property
    def email(self):
        return [dev.email for dev in self.developers if dev.primary_contact]

    @property
    def primary_contact(self):
        return [dev for dev in self.developers if dev.primary_contact][0]

    @property
    def submitted_games(self):
        return [g for g in self.games if g.submitted]

    @property
    def comped_badges(self):
        return c.INDIE_BADGE_COMPS * len([g for g in self.games if g.status == c.ACCEPTED])

    @property
    def unclaimed_badges(self):
        return max(0, self.comped_badges - len([d for d in self.developers if not d.matching_attendee]))


class IndieDeveloper(MagModel):
    studio_id       = Column(UUID, ForeignKey('indie_studio.id'))
    primary_contact = Column(Boolean, default=False)  # just means they receive emails
    first_name      = Column(UnicodeText)
    last_name       = Column(UnicodeText)
    email           = Column(UnicodeText)
    cellphone       = Column(UnicodeText)

    @property
    def full_name(self):
        return self.first_name + ' ' + self.last_name

    @property
    def matching_attendee(self):
        return self.session.query(Attendee).filter(
            func.lower(Attendee.first_name) == self.first_name.lower(),
            func.lower(Attendee.last_name) == self.last_name.lower(),
            func.lower(Attendee.email) == self.email.lower()
        ).first()


class IndieGame(MagModel, ReviewMixin):
    studio_id         = Column(UUID, ForeignKey('indie_studio.id'))
    title             = Column(UnicodeText)
    brief_description = Column(UnicodeText)
    genres            = Column(MultiChoice(c.INDIE_GENRE_OPTS))
    platforms         = Column(MultiChoice(c.INDIE_PLATFORM_OPTS))
    platforms_text    = Column(UnicodeText)
    description       = Column(UnicodeText)       # 500 max
    how_to_play       = Column(UnicodeText)       # 1000 max
    link_to_video     = Column(UnicodeText)
    link_to_game      = Column(UnicodeText)
    password_to_game  = Column(UnicodeText)
    code_type         = Column(Choice(c.CODE_TYPE_OPTS), default=c.NO_CODE)
    code_instructions = Column(UnicodeText)
    build_status      = Column(Choice(c.BUILD_STATUS_OPTS), default=c.PRE_ALPHA)
    build_notes       = Column(UnicodeText)       # 500 max
    shown_events      = Column(UnicodeText)
    video_submitted   = Column(Boolean, default=False)
    submitted         = Column(Boolean, default=False)
    agreed_liability  = Column(Boolean, default=False)
    agreed_showtimes  = Column(Boolean, default=False)
    agreed_reminder1  = Column(Boolean, default=False)
    agreed_reminder2  = Column(Boolean, default=False)
    status            = Column(Choice(c.GAME_STATUS_OPTS), default=c.NEW, admin_only=True)
    alumni_years      = Column(MultiChoice(c.PREV_MIVS_YEAR_OPTS))
    alumni_update     = Column(UnicodeText)
    judge_notes       = Column(UnicodeText, admin_only=True)
    registered        = Column(UTCDateTime, server_default=utcnow())

    codes = relationship('IndieGameCode', backref='game')
    reviews = relationship('IndieGameReview', backref='game')
    screenshots = relationship('IndieGameScreenshot', backref='game')

    email_model_name = 'game'

    @property
    def email(self):
        return self.studio.email

    @property
    def video_href(self):
        return href(self.link_to_video)

    @property
    def href(self):
        return href(self.link_to_game)

    @property
    def missing_steps(self):
        steps = []
        if not self.link_to_game:
            steps.append('You have not yet included a link to where the judges can access your game')
        if self.code_type != c.NO_CODE and self.link_to_game:
            if not self.codes:
                steps.append('You have not yet attached any codes to this game for our judges to use')
            elif not self.unlimited_code and len(self.codes) < c.CODES_REQUIRED:
                steps.append('You have not attached the {} codes you must provide for our judges'.format(c.CODES_REQUIRED))
        if not self.agreed_showtimes:
            steps.append('You must agree to the showtimes detailed on the game form (click the Edit link above)')
        if not self.agreed_liability:
            steps.append('You must check the box that agrees to our liability waiver (click the Edit link above)')
        return steps

    @property
    def video_broken(self):
        for r in self.reviews:
            if r.video_status == c.BAD_LINK:
                return True

    @property
    def unlimited_code(self):
        for code in self.codes:
            if code.unlimited_use:
                return code

    @property
    def video_submittable(self):
        return bool(self.link_to_video)

    @property
    def submittable(self):
        return not self.missing_steps

    @property
    def scores(self):
        return [r.game_score for r in self.reviews if r.game_score]

    @property
    def score_sum(self):
        return sum(self.scores, 0)

    @property
    def average_score(self):
        return (self.score_sum / len(self.scores)) if self.scores else 0

    @property
    def has_issues(self):
        return any(r.has_issues for r in self.reviews)

    @property
    def confirmed(self):
        return self.status == c.ACCEPTED and self.studio and self.studio.group_id


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
    video_status       = Column(Choice(c.VIDEO_REVIEW_STATUS_OPTS), default=c.PENDING)
    game_status        = Column(Choice(c.GAME_REVIEW_STATUS_OPTS), default=c.PENDING)
    game_content_bad   = Column(Boolean, default=False)
    video_score        = Column(Choice(c.VIDEO_REVIEW_OPTS), default=c.PENDING)
    game_score         = Column(Integer, default=0)  # 0 = not reviewed, 1-10 score (10 is best)
    video_review       = Column(UnicodeText)
    game_review        = Column(UnicodeText)
    developer_response = Column(UnicodeText)
    staff_notes        = Column(UnicodeText)

    __table_args__ = (UniqueConstraint('game_id', 'judge_id', name='review_game_judge_uniq'),)

    @presave_adjustment
    def no_score_if_broken(self):
        if self.has_video_issues:
            self.video_score = c.PENDING
        if self.has_game_issues:
            self.game_score = 0

    @property
    def has_video_issues(self):
        return self.video_status in c.PROBLEM_STATUSES

    @property
    def has_game_issues(self):
        return self.game_status in c.PROBLEM_STATUSES

    @property
    def has_issues(self):
        return self.has_video_issues or self.has_game_issues


@on_startup
def add_applicant_restriction():
    """
    We use convenience functions for our form handling, e.g. to instantiate an
    attendee from an id or from form data we use the session.attendee() method.
    This method runs on startup and overrides the methods which are used for the
    game application forms to add a new "applicant" parameter.  If truthy, this
    triggers three additional behaviors:
    1) We check that there is currently a logged in studio, and redirect to the
       initial application form if there is not.
    2) We check that the item being edited belongs to the currently-logged-in
       studio and raise an exception if it does not.  This check is bypassed for
       new things which have not yet been saved to the database.
    3) If the model is one with a "studio" relationship, we set that to the
       currently-logged-in studio.

    We do not perform these kinds of checks for indie judges, for two reasons:
    1) We're less concerned about judges abusively editing each other's reviews.
    2) There are probably some legitimate use cases for one judge to be able to
       edit another's reviews, e.g. to correct typos or reset a review's status
       after a link has been fixed, etc.
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
