# 🚄 RailInsight — Exploring TGV Punctuality

> An interactive Web application for analyzing punctuality of the SNCF's high-speed trains (TGV), built on SNCF open data.

## ☰ Table of Contents
- [Context](#context)
- [Instigation Goals](#investigation-g)
- [Data](#data)
- [Delivrables](#delivrables)
- [Tech Stack](#tech-stack)
- [Project Structure](#proj-struct)
- [Installation](#installation)
- [Usage](#usage)

  ---
 
## 🌐 Context <a name="context"></a>

> **TO COMPLETE: Context of the project**

## 🔎 Instigation Goals <a name="investigation-g"></a>

> **TO COMPLETE: the question guiding your study**

## 🛢️ Data <a name="data"></a>
 
- **Source**: [Monthly TGV Punctuality — SNCF Open Data](https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/information/)
- **Content**: for each month and route (departure / arrival station): scheduled trains, cancellations, delays at departure and arrival, average delays, and the breakdown of delay causes (external, infrastructure, traffic management, rolling stock, station management, passenger handling).
- **Local paths**: **TO COMPLETE**

## 📦 Delivrables <a name="delivrables"></a>

> **TO COMPLETE: the question guiding your study**

## 🛠️ Tech Stack <a name="tech-stack"></a>
 
| Area | Tools |
|---|---|
| Language | Python 3.xx |
| Environment management | `uv` |
| Web app | `Streamlit` |
| Analysis / visualisation | **TO COMPLETE** |
| Testing | **TO COMPLETE** |
| Code quality | `black` `ruff` |
| Documentation | **TO COMPLETE** |
| CI/CD | `GitHub Actions` |

## 🗂️ Project Structure <a name="proj-struct"></a>

> **TO COMPLETE: the question guiding your study**

## 📥 Installation <a name="installation"></a>

> **TO COMPLETE: the question guiding your study**

Pour installer le projet, exécutez ces commandes dans votre terminal :
git clone <url-du-repo>
cd RailInsight
uv sync

---

## 🧩 Usage <a name="usage"></a>

> **TO COMPLETE: the question guiding your study**

> ⚠️ **Alerte Architecture & Dépendance (Partie 2 - Socle du Projet) :** L'ensemble des analyses, des visualisations graphiques et de l'application Streamlit dépend entièrement du pipeline de nettoyage développé dans la Partie 2 (`src/railinsight/data_cleaning.py`). Avant de développer vos propres modules, assurez-vous que vos scripts s'appuient toujours sur le DataFrame propre et normalisé généré par la classe `TGVDataset`.

### 1. Lancer le pipeline de nettoyage (Script Principal)
Commande : uv run python src/railinsight/main.py

### 2. Utilisation dans vos scripts d'analyse
from railinsight.data_cleaning import TGVDataset, URL_SNCF, FICHIER_LOCAL

Initialisation du gestionnaire de dataset (socle commun de l'équipe)
dataset = TGVDataset(url=URL_SNCF, chemin_cache=FICHIER_LOCAL)

Récupération du DataFrame propre pour vos analyses
df_propre = dataset.nettoyer_donnees()

### 3. Contrôle qualité et Tests (Obligatoire avant chaque push)
Avant de proposer une fusion sur la branche principale, exécutez ces commandes :
- Tests unitaires et couverture : uv run python -m pytest --cov=railinsight --cov-report=term-missing
- Vérification du style et des imports : uv run python -m ruff check .
- Formatage automatique : uv run python -m black .
