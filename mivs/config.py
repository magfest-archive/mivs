from mivs import *
from uber.config import dynamic

mivs_config = parse_config(__file__)
c.include_plugin_config(mivs_config)

c.MIVS_CODES_REQUIRING_INSTRUCTIONS = [getattr(c, code_type.upper()) for code_type in c.MIVS_CODES_REQUIRING_INSTRUCTIONS]

# Add the access levels we defined to c.ACCESS* (this will go away if/when we implement enum merging)
c.ACCESS.update(c.MIVS_INDIE_ACCESS_LEVELS)
c.ACCESS_OPTS.extend(c.MIVS_INDIE_ACCESS_LEVEL_OPTS)
c.ACCESS_VARS.extend(c.MIVS_INDIE_ACCESS_LEVEL_VARS)

# c.MIVS_INDIE_JUDGE_GENRE* should be the same as c.MIVS_INDIE_GENRE* but with a c.MIVS_ALL_GENRES option
_mivs_all_genres_desc = 'All genres'
c.create_enum_val('mivs_all_genres')
c.make_enum('mivs_indie_judge_genre', mivs_config['enums']['mivs_indie_genre'])
c.MIVS_INDIE_JUDGE_GENRES[c.MIVS_ALL_GENRES] = _mivs_all_genres_desc
c.MIVS_INDIE_JUDGE_GENRE_OPTS.insert(0, (c.MIVS_ALL_GENRES, _mivs_all_genres_desc))

c.MIVS_PROBLEM_STATUSES = {getattr(c, status.upper()) for status in c.MIVS_PROBLEM_STATUSES.split(',')}

c.FINAL_MIVS_GAME_STATUSES = [c.ACCEPTED, c.WAITLISTED, c.DECLINED, c.STUDIO_DECLINED]

# used for computing the difference between the "drop-dead deadline" and the "soft deadline"
c.SOFT_MIVS_JUDGING_DEADLINE = c.MIVS_JUDGING_DEADLINE - timedelta(days=7)

# Automatically generates all the previous MIVS years based on the eschaton and c.MIVS_START_YEAR
c.PREV_MIVS_YEAR_OPTS, c.PREV_MIVS_YEARS = [], {}
for num in range(c.ESCHATON.year - c.MIVS_START_YEAR):
    val = c.MIVS_START_YEAR + num
    desc = c.EVENT_NAME + ' MIVS ' + str(val)
    c.PREV_MIVS_YEAR_OPTS.append((val, desc))
    c.PREV_MIVS_YEARS[val] = desc


def really_past_deadline(deadline):
    return localized_now() > (deadline + timedelta(minutes=c.MIVS_SUBMISSION_GRACE_PERIOD))


@Config.mixin
class IndieConfig:
    @property
    @dynamic
    def CAN_SUBMIT_ROUND_ONE(self):
        return not really_past_deadline(c.MIVS_ROUND_ONE_DEADLINE) or c.HAS_INDIE_ADMIN_ACCESS

    @property
    @dynamic
    def CAN_SUBMIT_ROUND_TWO(self):
        return not really_past_deadline(c.MIVS_ROUND_TWO_DEADLINE) or c.HAS_INDIE_ADMIN_ACCESS
