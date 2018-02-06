from mivs import *


def _is_invalid_url(url):
    if c.MIVS_SKIP_URL_VALIDATION:
        return False

    try:
        log.debug("_is_invalid_url() is fetching '%s' to check if it's reachable." % url)
        with urlopen(url, timeout=30) as f:
            f.read()
    except:
        return True


IndieStudio.required = [
    ('name', 'Studio Name'),
    ('website', 'Website')
]


@validation.IndieStudio
def new_studio_deadline(studio):
    if studio.is_new and not c.CAN_SUBMIT_MIVS_ROUND_ONE:
        return 'Sorry, but the round one deadline has already passed, so no new studios may be registered'


@validation.IndieStudio
def valid_url(studio):
    if studio.website and _is_invalid_url(studio.website_href):
        return 'We cannot contact that website; please enter a valid url or leave the website field blank until your website goes online'


@validation.IndieStudio
def unique_name(studio):
    with Session() as session:
        if session.query(IndieStudio).filter(IndieStudio.name == studio.name, IndieStudio.id != studio.id).count():
            return "That studio name is already taken; are you sure you shouldn't be logged in with that studio's account?"


IndieDeveloper.required = [('first_name', 'First Name'), ('last_name', 'Last Name'), ('email', 'Email')]


@validation.IndieDeveloper
def dev_email(dev):
    if not re.match(c.EMAIL_RE, dev.email):
        return 'Please enter a valid email address'


@validation.IndieDeveloper
def dev_cellphone(dev):
    from uber.model_checks import _invalid_phone_number
    if (dev.primary_contact or dev.cellphone) and _invalid_phone_number(dev.cellphone):
        return 'Please enter a valid phone number'


IndieGame.required = [
    ('title', 'Game Title'),
    ('brief_description', 'Brief Description'),
    ('genres', 'Genres'),
    ('description', 'Full Description'),
    ('link_to_video', 'Link to Video')
]


@validation.IndieGame
def platforms_or_other(game):
    if not game.platforms and not game.platforms_text:
        return 'Please select a platform your game runs on or describe another platform in the box provided.'


@validation.IndieGame
def new_game_deadline(game):
    if game.is_new and not c.CAN_SUBMIT_MIVS_ROUND_ONE:
        return 'Sorry, but the round one deadline has already passed, so no new games may be registered'


@validation.IndieGame
def instructions(game):
    if game.code_type in c.MIVS_CODES_REQUIRING_INSTRUCTIONS and not game.code_instructions:
        return 'You must leave instructions for how the judges are to use the code(s) you provide'


@validation.IndieGame
def video_link(game):
    if game.link_to_video and _is_invalid_url(game.video_href):
        return 'The link you provided for the intro/instructional video does not appear to work'


@validation.IndieGame
def submitted(game):
    if (game.submitted and not game.status == c.ACCEPTED) and not c.HAS_INDIE_ADMIN_ACCESS:
        return 'You cannot edit a game after it has been submitted'


@validation.IndieGame
def show_info_required_fields(game):
    if game.confirmed:
        if len(game.brief_description) > 80:
            return 'Please make sure your game has a brief description under 80 characters.'
        if not game.link_to_promo_video:
            return 'Please include a link to a 30-second promo video.'
        if game.has_multiplayer and not game.player_count:
            return 'Please tell us how many players your game supports.'
        if game.has_multiplayer and not game.multiplayer_game_length:
            return 'Please enter the average length for a multiplayer game or match.'


IndieGameCode.required = [('code', 'Game Code')]


@validation.IndieGameImage
def description(image):
    if image.is_screenshot and not image.description:
        return 'Please enter a description of the screenshot.'


@validation.IndieGameImage
def valid_type(screenshot):
    if screenshot.extension not in c.MIVS_ALLOWED_SCREENSHOT_TYPES:
        return 'Our server did not recognize your upload as a valid image'


IndieJudge.required = [('genres', 'Genres')]
