import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from colorlog import ColoredFormatter

def setup_logger(name: str) -> logging.Logger:
    """Configure et retourne un logger"""
    # Crée le dossier logs s'il n'existe pas
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Nom du fichier de log avec la date
    log_file = f'logs/{datetime.now().strftime("%Y-%m-%d")}-{name}.log'

    # Configuration du format pour la console (avec couleurs)
    console_formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )

    # Configuration du format pour le fichier
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Handler pour la console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)

    # Handler pour le fichier
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10485760,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)

    # Configuration du logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Supprime les handlers existants pour éviter les doublons
    logger.handlers.clear()
    
    # Ajoute les nouveaux handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger