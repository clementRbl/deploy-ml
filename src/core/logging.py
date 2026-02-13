import logging
import sys

from src.core.config import get_settings

settings = get_settings()


class ColoredFormatter(logging.Formatter):
    """Formatter qui ajoute des couleurs aux logs dans le terminal.

    Chaque niveau de log (DEBUG, INFO, WARNING, etc.) a sa propre couleur
    pour faciliter la lecture des logs pendant le développement.
    """

    # Codes ANSI pour les couleurs du terminal
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    # Mapping niveau de log -> format avec couleur
    FORMATS = {
        logging.DEBUG: grey + "%(levelname)s" + reset + " - %(message)s",
        logging.INFO: blue + "%(levelname)s" + reset + " - %(message)s",
        logging.WARNING: yellow + "%(levelname)s" + reset + " - %(message)s",
        logging.ERROR: red + "%(levelname)s" + reset + " - %(message)s",
        logging.CRITICAL: bold_red + "%(levelname)s" + reset + " - %(message)s",
    }

    def format(self, record):
        """Formate un message de log avec la couleur appropriée.

        Args:
            record: L'enregistrement de log à formater.

        Returns:
            str: Le message formaté avec les codes couleur ANSI.
        """
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logging() -> logging.Logger:
    """Configure le système de logging de l'application.

    Crée un logger nommé 'deploy_ml' avec :
    - Niveau de log configurable via settings.log_level (INFO par défaut)
    - Format texte avec couleurs en développement
    - Format JSON en production

    Returns:
        logging.Logger: Le logger configuré prêt à l'emploi.
    """
    logger = logging.getLogger("deploy_ml")
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Handler pour la sortie console (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    if settings.log_format == "text":
        # Développement : format texte avec couleurs
        console_handler.setFormatter(ColoredFormatter())
    else:
        # Production : format JSON pour agrégation de logs
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

    logger.addHandler(console_handler)
    return logger


# Instance globale importée partout : from src.core.logging import logger
logger = setup_logging()
