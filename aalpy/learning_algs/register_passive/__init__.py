import logging

handler = logging.FileHandler('error.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(name)s: %(message)s')
handler.setFormatter(formatter)

completable_logger = logging.getLogger('completable')
completable_logger.addHandler(handler)
# completable_logger.setLevel(logging.DEBUG)

transition_logger = logging.getLogger('transition')
transition_logger.addHandler(handler)
transition_logger.setLevel(logging.DEBUG)

learner_logger = logging.getLogger('learner')
learner_logger.addHandler(handler)
learner_logger.setLevel(logging.DEBUG)

refine_logger = logging.getLogger('refine')
refine_logger.addHandler(handler)
# refine_logger.setLevel(logging.DEBUG)

completable_logger = logging.getLogger('completable')
completable_logger.addHandler(handler)
completable_logger.setLevel(logging.DEBUG)

readword_logger = logging.getLogger('readword')
readword_logger.addHandler(handler)
# readword_logger.setLevel(logging.DEBUG)