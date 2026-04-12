import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Setup logging
log_dir = "logs/bot"
os.makedirs(log_dir, exist_ok=True)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Standard log handler
info_handler = RotatingFileHandler(f"{log_dir}/bot.log", maxBytes=10*1024*1024, backupCount=5)
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(formatter)

# Error log handler
error_handler = RotatingFileHandler(f"{log_dir}/bot.errors", maxBytes=10*1024*1024, backupCount=5)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(info_handler)
logger.addHandler(error_handler)
logger.addHandler(logging.StreamHandler())

from src.bot import main

if __name__ == "__main__":
    logger.info("Starting Danaa Bot...")
    main()
