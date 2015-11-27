from mivs import *


def assign_codes():
    if not c.PRE_CON:
        return

    with Session() as session:
        for game in session.indie_games():
            if game.code_type == c.NO_CODE or game.unlimited_code:
                continue

            for review in game.reviews:
                if not set(game.codes).intersection(review.judge.codes):
                    for code in game.codes:
                        if not code.judge_id:
                            code.judge = review.judge
                            session.commit()
                            break
                    else:
                        log.warning('unable to find free code for game {} to assign to judge {}', game.title, review.judge.full_name)

DaemonTask(assign_codes, interval=300)
