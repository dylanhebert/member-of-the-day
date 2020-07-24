# Member of the Day: Logger Configuration
#

import logging
import pathlib

DIR_PATH = str(pathlib.Path().absolute())

# LOGGER STUFF
logger = logging.getLogger('MOTD')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',datefmt='%m/%d/%Y %I:%M:%S %p')
ch = logging.StreamHandler()
fh = logging.FileHandler(DIR_PATH + '/logs.log')
ch.setLevel(logging.DEBUG)
fh.setLevel(logging.INFO)
ch.setFormatter(formatter)
fh.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(fh)