"""Configuration de la connexion à la base de données PostgreSQL.

Construit un moteur SQLAlchemy à partir des variables d'environnement de connexion
(``DB_USERNAME``, ``DB_PASSWORD``, ``DB_HOST``, ``DB_PORT``, ``DB_NAME``).
"""

import os

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.engine import Engine

load_dotenv()


def make_engine() -> Engine:
    """Crée et configure un moteur de connexion à la base de données PostgreSQL.

    Cette fonction récupère les paramètres de connexion à la base de données
    depuis les variables d'environnement, puis construit une URL de connexion
    SQLAlchemy à l'aide de ces paramètres.

    Le moteur SQLAlchemy est ensuite initialisé avec l'option ``pool_pre_ping=True``,
    qui permet de vérifier la validité des connexions avant leur utilisation.
    Cette vérification contribue à éviter les erreurs liées aux connexions
    interrompues ou devenues indisponibles dans le pool de connexions.

    Les variables d'environnement suivantes sont utilisées :

    - ``DB_USERNAME`` : nom d'utilisateur de la base de données.
    - ``DB_PASSWORD`` : mot de passe associé à l'utilisateur.
    - ``DB_HOST`` : adresse du serveur PostgreSQL.
    - ``DB_PORT`` : port d'écoute du serveur PostgreSQL.
    - ``DB_NAME`` : nom de la base de données à utiliser.

    Returns:
        Engine: Un moteur SQLAlchemy configuré pour communiquer avec la
        base de données PostgreSQL.

    Note:
        Le chargement des variables d'environnement est effectué au niveau
        du module avec ``load_dotenv()``. Le moteur est créé lors de l'appel
        de cette fonction, et non au chargement du module.

    Raises:
        sqlalchemy.exc.ArgumentError: Si l'URL de connexion fournie est invalide.
        sqlalchemy.exc.OperationalError: Si une connexion à la base de données
            échoue lors de son établissement.

    Example:
        >>> engine = make_engine()
        >>> print(engine.dialect.name)
        postgresql
    """

    url_object = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
    )
    engine = create_engine(url=url_object, pool_pre_ping=True)
    return engine
