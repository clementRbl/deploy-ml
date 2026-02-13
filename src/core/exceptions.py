class DeployMLError(Exception):
    """Exception de base pour l'application.

    Toutes les exceptions custom héritent de cette classe.
    Permet d'associer un message d'erreur à un code HTTP.
    """

    def __init__(self, message: str, status_code: int = 500):
        """Initialise l'exception avec un message et un code HTTP.

        Args:
            message: Le message d'erreur à afficher.
            status_code: Le code HTTP à retourner (défaut: 500).
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ModelNotLoadedError(DeployMLError):
    """Exception levée quand les modèles ML ne sont pas chargés.

    Retourne un code 503 (Service Unavailable) car l'API ne peut pas fonctionner
    sans les modèles chargés en mémoire.
    """

    def __init__(self, message: str = "Modèles non chargés"):
        """Initialise l'exception pour modèles non disponibles.

        Args:
            message: Le message d'erreur (défaut: "Modèles non chargés").
        """
        super().__init__(message, status_code=503)


class PredictionError(DeployMLError):
    """Exception levée lors d'une erreur de prédiction.

    Retourne un code 500 (Internal Server Error) car une erreur inattendue
    s'est produite pendant le calcul de la prédiction.
    """

    def __init__(self, message: str):
        """Initialise l'exception pour erreur de prédiction.

        Args:
            message: Le message décrivant l'erreur de prédiction.
        """
        super().__init__(f"Erreur de prédiction: {message}", status_code=500)


class InvalidInputError(DeployMLError):
    """Exception levée pour des données d'entrée invalides.

    Retourne un code 400 (Bad Request) car les données fournies par le client
    ne respectent pas le format attendu.
    """

    def __init__(self, message: str):
        """Initialise l'exception pour données invalides.

        Args:
            message: Le message décrivant pourquoi les données sont invalides.
        """
        super().__init__(f"Données invalides: {message}", status_code=400)
