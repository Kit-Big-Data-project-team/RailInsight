# RailInsight — Explorer la régularité des TGV

RailInsight est une application web interactive qui permet d'explorer les retards et les annulations des TGV à partir des données ouvertes publiées par SNCF Voyageurs. L'objectif est de rendre ces données plus faciles à consulter et à interpréter, en passant d'un jeu de données mensuelles à des indicateurs, des classements et des visualisations accessibles au grand public.

> **Accès rapides**
>
> - **Dépôt GitHub :** [Kit-Big-Data-project-team/RailInsight](https://github.com/Kit-Big-Data-project-team/RailInsight)
> - **Application déployée :** [Ouvrir RailInsight](https://railinsight-3zgyn2awwmnsklkuivzmdc.streamlit.app/)
> - **Documentation du jeu de données :** [Consulter la documentation](https://github.com/Kit-Big-Data-project-team/RailInsight/blob/main/docs/Documentation_du_jeu_de_données_Régularité_mensuelle_TGV.docx) 
> - **Documentation technique avec Sphinx :** Lancer ces deux commandes dans la racine du projet afin de générer la documentation Sphinx
`python -m sphinx -E -b html docs docs/build/html`  
`start docs/build/html/index.html`

## 1. Contexte et objectifs

Le projet a été réalisé dans le cadre du module **IADATA700 - Kit Big Data**. Le scénario retenu est celui d'une jeune structure, RailInsight, chargée de fournir à un grand quotidien national une application web publique consacrée à la ponctualité des TGV. L'application doit permettre aux lecteurs d'explorer les chiffres derrière les retards, plutôt que de se limiter à un constat général.

La question qui guide ce travail est la suivante :

**Les retards des TGV sont-ils des incidents isolés ou révèlent-ils des difficultés récurrentes ? Où, quand et pour quelles raisons surviennent-ils ?**

Pour apporter des éléments de réponse, l'application propose cinq angles de lecture :

1. **Comprendre la situation d'ensemble** grâce à des indicateurs clés et à une présentation des différentes pages.
2. **Suivre les évolutions** des retards et des annulations au fil des mois, en observant notamment les causes déclarées et la saisonnalité.
3. **Comparer les liaisons** à l'aide d'un classement des plus fiables et des moins fiables.
4. **Examiner un trajet précis** en sélectionnant une liaison entre une gare de départ et une gare d'arrivée.
5. **Anticiper les retards mensuels** en prévoyant le taux de retard d'une liaison TGV pour le mois suivant à partir des données historiques.

Le projet couvre également toute la chaîne technique : récupération des données par API et mise à jour automatique de ces derniéres, préparation et nettoyage avec Python, stockage dans PostgreSQL, puis restitution dans une application Streamlit.

## 2. L'application

L'application est organisée en cinq pages accessibles depuis la navigation Streamlit.

| Page | Contenu |
|---|---|
| **Vue d'ensemble** | Présente une synthèse de la ponctualité des liaisons TGV du jeu de données : nombre de liaisons suivies, volume total de circulations prévues, taux de retard et d'annulation du dernier mois disponible. La page propose également une évolution mensuelle des retards et des annulations, trois observations clés sur la tendance récente, le mois au taux de retard le plus élevé et la principale cause de retard, ainsi qu'une répartition des causes et une visualisation de la saisonnalité. |
| **Historique & évolution** | Permet d'analyser les retards et les annulations sur l'ensemble des liaisons ou sur une liaison sélectionnée, avec un filtre temporel. La page présente les taux de retard, d'annulation et de perturbation, leur évolution mensuelle, les périodes les plus perturbées, une comparaison entre services nationaux et internationaux, la sévérité des retards (15, 30 et 60 minutes), l'évolution des causes déclarées et une comparaison par mois de l'année. |
| **Fiabilité des liaisons** | Classe les dix liaisons les plus fiables et les dix moins fiables selon leur score de fiabilité, avec un seuil minimal de trafic configurable. La page permet également de visualiser les taux de retard et d'annulation par liaison en tenant compte du volume de circulation, de comparer les services nationaux et internationaux et de consulter les tableaux détaillés des classements. |
| **Mon trajet** | Permet de sélectionner une liaison et une période pour consulter ses indicateurs historiques : taux d'annulation, taux de retard, taux de perturbation et retard moyen à l'arrivée. La page présente également la répartition des issues sur une base de 100 circulations prévues, compare les douze derniers mois aux douze mois précédents lorsque les données le permettent, compare les deux sens de circulation et affiche les causes déclarées des retards. |
| **Prédiction des retards** | Permet de prévoir automatiquement le taux de retard du mois n+1, où n correspond au dernier mois disponible dans les données SNCF, à partir des trois derniers mois observés. La page utilise un modèle Random Forest et présente une carte interactive des liaisons TGV, les prévisions, l'évolution historique des retards et une comparaison des performances du modèle avec une méthode de référence. |

Les visualisations sont réalisées avec **Plotly**, **Streamlit** et **PyDeck**. Les pages chargent les données depuis PostgreSQL et utilisent une couche commune de préparation afin de conserver les mêmes noms de colonnes et les mêmes définitions d'indicateurs d'une page à l'autre.

> **Périmètre des indicateurs.** Le jeu SNCF (AQST) décrit la régularité **par liaison** : un même train peut être comptabilisé dans plusieurs liaisons. Les agrégats présentés dans l'application portent donc sur les observations des liaisons du jeu de données ; ils ne représentent pas la régularité nationale officielle des TGV et ne doivent pas être additionnés pour en déduire un taux « réseau » global. [Voir la précision de la SNCF](https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/information/).

## 3. Données utilisées

### Source

Le projet utilise le jeu de données **[« Régularité mensuelle TGV par liaisons (AQST) » — SNCF Open Data](https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/)**, publié par SNCF Voyageurs.

L'application récupère les enregistrements depuis l'API du portail SNCF Open Data. L'URL d'export JSON utilisée par le projet est configurée dans le fichier `.env` :

```text
https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/regularite-mensuelle-tgv-aqst/exports/json
```

### Périmètre de la version documentée

Les chiffres ci-dessous correspondent à l'extraction décrite dans la documentation du jeu de données fournie avec le projet. Ils caractérisent cette version de référence (jusqu'à septembre 2026) et peuvent évoluer lors des prochaines mises à jour de la source.

| Indicateur | Valeur documentée |
|---|---:|
| Nombre d'enregistrements | 12 907 |
| Nombre de colonnes dans l'export d'origine | 26 |
| Période couverte | Janvier 2018 à septembre 2026 (105 mois) |
| Liaisons | 130 |
| Gares | 59 |
| Enregistrements de service national | 11 339 (environ 87 %) |
| Enregistrements de service international | 1 568 (environ 13 %) |

### Préparation des données

Le traitement réalisé dans `src/railinsight/data/data_cleaning.py` est volontairement centré sur la mise en forme et la normalisation des données. Il suit les étapes suivantes :

1. Conversion de la réponse de l'API (liste de dictionnaires) en DataFrame Pandas.
2. Suppression des lignes entièrement vides.
3. Normalisation des noms de colonnes : suppression des espaces superflus, passage en minuscules et remplacement des espaces par des underscores.
4. Suppression des colonnes dont plus de 90 % des valeurs sont manquantes. Cette règle concerne notamment les champs de commentaires dans l'extraction étudiée.
5. Conversion de la colonne `date` en date exploitable par PostgreSQL.
6. Création d'une colonne `liaison` à partir de la gare de départ et de la gare d'arrivée.
7. Conservation du schéma de colonnes attendu par la base de données.

Le nettoyage ne corrige pas automatiquement toutes les anomalies métier et ne cherche pas à dédupliquer les données. Le chargement utilisé par l'application écarte ensuite les lignes dont le nombre de circulations prévues est nul avant les analyses.

## 4. Architecture technique et flux de données

RailInsight repose sur une architecture organisée en plusieurs couches : collecte et préparation des données, stockage dans PostgreSQL, chargement et normalisation, analyses métier, puis visualisation dans une application Streamlit.

```text
              SNCF Open Data
                (API JSON)
                    |
                    v
        Récupération des données
               (Requests)
                    |
                    v
         Nettoyage et normalisation
                (Pandas)
                    |
                    v
          Vérification du schéma
                    |
                    v
          Base de données PostgreSQL
             Table regularite_tgv
                    |
                    v
             TGVDataset.from_db()
          Chargement et harmonisation
                    |
                    v
             Couche d'analyse
        (src/railinsight/analysis/)
                    |
                    v
          Couche de visualisation
          (src/railinsight/viz/)
                    |
                    v
            Application Streamlit
                 (views/)
                    |
                    v
       Vue d'ensemble | Historique
       Fiabilité      | Mon trajet
       Prédiction des retards
```

Le pipeline commence dans `src/railinsight/main.py`, qui initialise la base de données et lance le processus ETL.

Les données sont récupérées depuis l'API SNCF, nettoyées et préparées dans `src/railinsight/data/`, puis stockées dans PostgreSQL, dans la table `regularite_tgv`. Le module `loader.py` fournit la classe `TGVDataset`, qui charge et harmonise les données pour les différentes pages de l'application.

Le chargement est **idempotent** : à chaque exécution, l'ETL réinterroge l'API sur les derniers mois déjà présents (fenêtre de reprise) et applique un `INSERT ... ON CONFLICT DO UPDATE` sur la clé `(date, service, gare_depart, gare_arrivee)`. Relancer le pipeline ne crée donc pas de doublon, et une éventuelle rectification publiée par la SNCF sur un mois récent remplace l'ancienne valeur.

Les données sont ensuite exploitées par deux couches :
- **`analysis/`** : calcule les indicateurs, agrégations, classements et comparaisons.
- **`viz/`** : regroupe les fonctions de visualisation, notamment les graphiques Plotly et la carte interactive PyDeck. Le module `theme.py` centralise les couleurs et le thème graphique commun.

Enfin, le dossier `views/` regroupe les cinq pages Streamlit, qui utilisent ces couches pour présenter les résultats.

Cette architecture sépare la collecte, le stockage, l'analyse et la visualisation, tout en favorisant la réutilisation du code.

## 5. Structure du dépôt

La structure ci-dessous reprend les principaux dossiers et fichiers du dépôt. Elle donne le rôle des grandes zones du projet sans détailler chaque module.

```text
RailInsight/
│
├── .github/
│   └── workflows/              # Workflows d'intégration continue
│
├── .streamlit/
│   └── config.toml             # Configuration de l'application Streamlit
│
├── docker/                     # Scripts liés au démarrage des conteneurs
│
├── docs/
│   ├── DEPLOYMENT.md           # Instructions de déploiement
│   └── Documentation_du_jeu_de_données_Régularité_mensuelle_TGV.docx
│                               # Documentation du jeu de données
│
├── logs/                       # Fichiers de journalisation
│
├── src/
│   └── railinsight/
│       │
│       ├── analysis/           # Calculs des indicateurs et analyses métier 
│       │
│       ├── data/               # Collecte, nettoyage et chargement des données
│       │
│       ├── database/           # Connexion et gestion de PostgreSQL
│       │
│       ├── viz/                # Fonctions de visualisation Plotly
│       │
│       ├── exceptions.py       # Exceptions propres au projet
│       ├── logging_config.py   # Configuration des journaux
│       └── main.py             # Point d'entrée du pipeline ETL
│
├── tests/                      # Tests automatisés
│
├── views/                      # Pages de l'application Streamlit
│   ├── overview.py             # Vue d'ensemble
│   ├── history.py              # Historique et évolution
│   ├── reliability.py          # Fiabilité des liaisons
│   ├── trip.py                 # Analyse d'une liaison
│   └── prediction.py           # Prédiction des retards et carte interactive
│
├── .dockerignore               # Fichiers exclus de la construction Docker
├── .env.example                # Exemple de variables d'environnement
├── .gitignore                  # Fichiers exclus du suivi Git
├── Dockerfile                  # Construction de l'image applicative
├── docker-compose.yml          # Orchestration PostgreSQL et Streamlit
├── pyproject.toml              # Dépendances et configuration du projet
├── requirements.txt            # Dépendances Python
├── streamlit_app.py            # Point d'entrée et navigation Streamlit
└── uv.lock                     # Verrouillage des dépendances
```

## 6. Technologies utilisées

| Besoin | Outils |
|---|---|
| Langage | Python 3.11 ou supérieur |
| Gestion de l'environnement et des dépendances | `uv` |
| Application web | Streamlit |
| Manipulation des données | Pandas |
| Graphiques | Plotly et graphiques natifs Streamlit |
| Appels à l'API | Requests |
| Accès à la base | SQLAlchemy et `psycopg2-binary` |
| Base de données | PostgreSQL 17 (image Docker `postgres:17-alpine`) |
| Configuration locale | `python-dotenv` et variables d'environnement |
| Tests | Pytest et pytest-cov |
| Qualité du code | Ruff et Black |
| Documentation technique | Sphinx |
| Conteneurisation | Docker et Docker Compose |
| Intégration continue | GitHub Actions |
| Machine learning et prédiction | Scikit-learn (Random Forest Regressor) |
| Cartographie interactive | PyDeck (fonds cartographiques OpenStreetMap / CARTO) |

## 7. Lancer RailInsight en local avec Docker

Le dépôt contient un `docker-compose.yml` qui démarre **PostgreSQL et l'application Streamlit**. C'est la méthode recommandée pour tester le projet.

### Prérequis

- Git ;
- Docker Desktop (Windows ou macOS) ou Docker Engine (Linux) ;
- Docker Compose v2, accessible avec la commande `docker compose` ;
- une connexion Internet lors du chargement initial, afin de récupérer les données depuis l'API SNCF.

### Étape 1 — Récupérer le dépôt

```bash
git clone https://github.com/Kit-Big-Data-project-team/RailInsight.git
cd RailInsight
```

### Étape 2 — Préparer le fichier `.env`

Copier le fichier d'exemple :

**Linux / macOS / Git Bash :**

```bash
cp .env.example .env
```

**Windows PowerShell :**

```powershell
Copy-Item .env.example .env
```

Ouvrir ensuite `.env` et renseigner les variables de connexion. Exemple de configuration pour une exécution avec Docker Compose :

```dotenv
DB_USERNAME=railinsight
DB_PASSWORD=mot_de_passe
DB_HOST=db
DB_PORT=5432
DB_NAME=railinsight
URl_SNCF_DATASET=https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/regularite-mensuelle-tgv-aqst/exports/json
```

Les valeurs `railinsight` et `mot_de_passe` sont des exemples : vous pouvez choisir vos propres identifiants. Le nom de variable `URl_SNCF_DATASET` est écrit exactement comme dans le code actuel et dans `.env.example` ; il faut conserver cette casse, même si elle peut sembler inhabituelle.

Dans le réseau Docker Compose, l'application se connecte à PostgreSQL avec `DB_HOST=db` : `db` est le nom du service déclaré dans `docker-compose.yml`. Le port `5432` est publié sur la machine hôte et le port `8501` est utilisé pour l'application Streamlit.

### Étape 3 — Construire et démarrer les services

À la racine du projet, exécuter :

```bash
docker compose up --build
```

Au premier démarrage, Docker effectue les opérations suivantes :

1. construit l'image de l'application à partir du `Dockerfile` ;
2. démarre le conteneur PostgreSQL ;
3. attend que la base soit disponible grâce au healthcheck ;
4. initialise la base (étape **bloquante** : si la base est inaccessible ou le schéma incompatible, le démarrage s'arrête avec une erreur explicite plutôt que de lancer une application vide) ;
5. lance le pipeline ETL : récupère les données SNCF, les nettoie et les insère ou met à jour dans PostgreSQL (UPSERT idempotent) ;
6. démarre le serveur Streamlit.

L'application est ensuite accessible à l'adresse suivante :

**http://localhost:8501**

Le premier lancement peut être plus long que les suivants, car la base doit être initialisée et alimentée avec les données disponibles sur l'API.

### Étape 4 — Arrêter l'application

Dans le terminal où Docker Compose est lancé, utiliser `Ctrl + C`, puis :

```bash
docker compose down
```

Les données PostgreSQL sont conservées dans le volume Docker `postgres_data`. Ainsi, arrêter puis redémarrer les conteneurs ne supprime pas les données déjà chargées.

Pour redémarrer ultérieurement les services :

```bash
docker compose up
```

Pour supprimer également le volume et donc effacer la base locale :

```bash
docker compose down -v
```

> **Attention :** `docker compose down -v` supprime les données stockées dans PostgreSQL. À utiliser uniquement pour repartir volontairement d'une base vide.

### Quelques commandes utiles

Consulter les logs de l'application :

```bash
docker compose logs -f app
```

Consulter les logs de PostgreSQL :

```bash
docker compose logs -f db
```

Relancer manuellement l'initialisation et le pipeline depuis le conteneur applicatif :

```bash
docker compose exec app uv run --no-sync python src/railinsight/main.py
```

Si l'API SNCF est temporairement indisponible, seule l'étape ETL est ignorée : Streamlit se lance tout de même avec les données déjà présentes en base. En revanche, une erreur d'**initialisation de la base** (base inaccessible ou schéma incompatible) est bloquante et arrête le démarrage, afin de ne pas présenter une application sans données en la faisant passer pour fonctionnelle. Si la base est encore vide, il faut consulter les logs et relancer le pipeline lorsque l'API est de nouveau accessible.

## 8. Variante : lancer Streamlit sur la machine hôte

Il est aussi possible de conserver PostgreSQL dans Docker et de lancer Streamlit directement depuis l'environnement Python local. Cette variante est utile pour développer l'application sans reconstruire l'image Docker à chaque modification.

Après avoir préparé le fichier `.env`, régler `DB_HOST` sur `localhost` pour cette exécution hors du réseau Compose :

```dotenv
DB_HOST=localhost
DB_PORT=5432
```

Démarrer uniquement PostgreSQL :

```bash
docker compose up -d db
```

Installer les dépendances du projet avec `uv` :

```bash
uv sync
```

Si la base vient d'être créée et ne contient pas encore de données, lancer le pipeline :

```bash
uv run python src/railinsight/main.py
```

Puis démarrer Streamlit :

```bash
uv run streamlit run streamlit_app.py
```

L'application sera disponible sur **http://localhost:8501**. Dans cette configuration, le service PostgreSQL reste accessible sur le port `5432` de la machine hôte.

## 9. Tests et qualité du code

Les tests automatisés se trouvent dans le dossier `tests/`. Depuis la racine du dépôt, les principales commandes sont :

```bash
# Lancer les tests
uv run pytest

# Lancer les tests avec un rapport de couverture
uv run pytest --cov=railinsight --cov-report=term-missing

# Vérifier le style et les imports
uv run ruff check .

# Vérifier le formatage
uv run black --check .
```

Pour appliquer automatiquement le formatage Black :

```bash
uv run black .
```

Les workflows GitHub Actions du dépôt permettent d'automatiser une partie des contrôles du projet. Les dépendances de développement (tests, qualité et documentation) sont déclarées dans `pyproject.toml` et verrouillées avec `uv.lock`.

## 10. Logs et documentation technique

La configuration de journalisation se trouve dans `src/railinsight/logging_config.py`. Elle crée le dossier `logs/` si nécessaire et écrit deux fichiers :

- `logs/debug.log` pour les événements à partir du niveau DEBUG ;
- `logs/errors.log` pour les erreurs à partir du niveau ERROR.

Le dossier `docs/` est prévu pour la documentation du projet. La configuration Sphinx et les dépendances associées sont déclarées dans le dépôt ; les documents de présentation et la documentation du dataset peuvent également y être déposés pour centraliser les livrables.

## 11. Livrables du projet

Les livrables sont regroupés autour de cinq éléments complémentaires :

1. **Le dépôt GitHub** : le code source, les tests, les fichiers Docker, la configuration et la documentation technique de l'application.
2. **L'application déployée** : une version accessible en ligne pour découvrir les analyses sans installer le projet. [RailInsight — application en ligne](https://railinsight-3zgyn2awwmnsklkuivzmdc.streamlit.app/).
3. **La documentation du jeu de données** : la description de la source, du schéma, de la collecte, des traitements, des limites et des conditions de réutilisation.
4. **Le présent README** : le guide d'entrée du dépôt, qui explique le fonctionnement de l'application et la façon de la lancer en local.
5. **Documentation Sphinx** : documentation générée avec Sphinx, présentant l'architecture du projet ainsi que les modules, fonctions et méthodes Python.

## 12. Source des données et licence

Le jeu de données est publié par **SNCF Voyageurs** sous licence **Open Database License (ODbL)**. Toute réutilisation des données doit respecter les conditions de cette licence et conserver l'attribution de la source.

Référence : [Régularité mensuelle TGV par liaisons — SNCF Open Data](https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/).

Les indicateurs, agrégations et visualisations présentés dans RailInsight sont des traitements réalisés dans le cadre du projet à partir de cette source.
