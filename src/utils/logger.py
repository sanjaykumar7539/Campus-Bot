import logging
import sys
from pathlib import Path

def get_logger(name: str = "college_chatbot"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        console.setFormatter(formatter)
        logger.addHandler(console)
        Path("logs").mkdir(exist_ok=True)
        file_handler = logging.FileHandler("logs/chatbot.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger
