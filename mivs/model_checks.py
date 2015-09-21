from mivs import *

def _is_invalid_url(url):
    try:
        with urlopen(url) as f:
            f.read()
    except:
        return True


IndieStudio.required = [('name', 'Studio Name')]


@validation.IndieStudio
def valid_url(studio):
    if studio.website and _is_invalid_url(studio.website):
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
    ('link_to_game', 'Link to Game'),
]


@validation.IndieGame
def instructions(game):
    if game.code_type != c.NO_CODE and not game.code_instructions:
        return 'You must leave instructions for how the judges are to use the code(s) you provide'


@validation.IndieGame
def video_link(game):
    if game.link_to_video and _is_invalid_url(game.link_to_video):
        return 'The link you provided for the intro/instructional video does not appear to work'


@validation.IndieGame
def agreements(game):
    if not game.agreed_showtimes:
        return 'You must agree to showtimes, or something'  # TODO: figure out what this is
    elif not game.agreed_liability:
        return 'You must check the box that indicates you agree to our liability waiver'
