from mivs import *

mivs_config = parse_config(__file__)
c.include_plugin_config(mivs_config)

c.CODES_REQUIRING_INSTRUCTIONS = [getattr(c, code_type.upper()) for code_type in c.CODES_REQUIRING_INSTRUCTIONS]
