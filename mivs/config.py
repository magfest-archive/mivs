from mivs import *

mivs_config = parse_config(__file__)
c.include_plugin_config(mivs_config)

c.CODES_REQUIRING_INSTRUCTIONS = [getattr(c, code_type.upper()) for code_type in c.CODES_REQUIRING_INSTRUCTIONS]

# Add the access levels we defined to c.ACCESS* (this will go away if/when we implement enum merging)
c.ACCESS.update(c.INDIE_ACCESS_LEVELS)
c.ACCESS_OPTS.extend(c.INDIE_ACCESS_LEVEL_OPTS)
c.ACCESS_VARS.extend(c.INDIE_ACCESS_LEVEL_VARS)

# c.INDIE_JUDGE_GENRE* should be the same as c.INDIE_GENRE* but with a c.ALL_GENRES option
_all_genres_desc = 'All genres'
c.create_enum_val('all_genres')
c.make_enum('indie_judge_genre', mivs_config['enums']['indie_genre'])
c.INDIE_JUDGE_GENRES[c.ALL_GENRES] = _all_genres_desc
c.INDIE_JUDGE_GENRE_OPTS.insert(0, (c.ALL_GENRES, _all_genres_desc))
