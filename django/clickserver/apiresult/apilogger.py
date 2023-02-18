import logging

logger = logging.getLogger('apiresult')
logger.setLevel(logging.DEBUG)

# create a file handler
handler = logging.FileHandler('apiresult.log')
handler.setLevel(logging.DEBUG)

# create a formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handler to the logger
logger.addHandler(handler)
