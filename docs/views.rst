Pages Streamlit
===============

Cette section présente les différentes pages de l'application RailInsight.

Vue d'ensemble
--------------

Présente une synthèse de la ponctualité des liaisons TGV du jeu de données : nombre de liaisons suivies,
volume total de circulations prévues, taux de retard et d'annulation du dernier mois disponible.
La page propose également une évolution mensuelle des retards et des annulations,
trois observations clés sur la tendance récente, le mois au taux de retard le plus élevé et la principale cause de retard,
ainsi qu'une répartition des causes et une visualisation de la saisonnalité.

.. note::

   Le jeu SNCF (AQST) décrit la régularité **par liaison** : un même train peut être comptabilisé
   dans plusieurs liaisons. Les agrégats de cette page portent sur les observations des liaisons du
   jeu de données ; ils ne représentent pas la régularité nationale officielle des TGV.

Historique
----------
Permet d'analyser les retards et les annulations sur l'ensemble des liaisons ou sur une liaison sélectionnée,
avec un filtre temporel. La page présente les taux de retard, d'annulation et de perturbation,
leur évolution mensuelle, les périodes les plus perturbées, une comparaison entre services nationaux et internationaux,
la sévérité des retards (15, 30 et 60 minutes), 
l'évolution des causes déclarées et une comparaison par mois de l'année.

Fiabilité
---------

Classe les dix liaisons les plus fiables et les dix moins fiables selon leur score de fiabilité, 
avec un seuil minimal de trafic configurable. La page permet également de visualiser les taux de retard et 
d'annulation par liaison en tenant compte du volume de circulation, 
de comparer les services nationaux et internationaux et de consulter les tableaux détaillés des classements.

Mon trajet
----------

Permet de sélectionner une liaison et une période pour consulter ses indicateurs historiques : 
taux d'annulation, taux de retard, taux de perturbation et retard moyen à l'arrivée. 
La page présente également la répartition des issues sur une base de 100 circulations prévues, 
compare les douze derniers mois aux douze mois précédents lorsque les données le permettent, 
compare les deux sens de circulation et affiche les causes déclarées des retards.

Prédiction des retards
----------------------

Permet de sélectionner une liaison TGV et un service pour prévoir le taux de retard du mois suivant à l'aide d'un modèle Random Forest.
La prévision est dynamique : si ``n`` représente le dernier mois disponible dans les données SNCF, le modèle prédit le mois ``n+1`` en utilisant
les taux de retard des trois derniers mois consécutifs observés (``n``, ``n-1`` et ``n-2``). Le mois prévu est toujours ``n+1`` par rapport au dernier mois
disponible dans **tout** le jeu de données, jamais au dernier mois propre à une liaison inactive.
La page affiche également une carte interactive des gares de départ et d'arrivée, reliées par un tracé indicatif, ainsi que l'évolution
historique des retards et une comparaison des performances du modèle avec une méthode de référence.

Fiabilité de la prévision
-------------------------

Prolonge la prédiction ponctuelle par une évaluation honnête de sa fiabilité. La page encadre chaque prévision d'une **fourchette d'incertitude**
(régression par quantiles, intervalle à 80 %), mesure la robustesse du modèle **mois par mois** par un backtesting glissant comparé à une méthode
de référence, et vérifie que l'incertitude annoncée est **calibrée** (la part des valeurs réelles tombant dans l'intervalle doit avoisiner 80 %).
La prévision du mois suivant reste disponible même pour une liaison ne comptant que trois mois consécutifs d'historique.