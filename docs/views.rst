Pages Streamlit
===============

Cette section présente les différentes pages de l'application RailInsight.

Vue d'ensemble
--------------

Présente une synthèse de la ponctualité du réseau TGV : nombre de liaisons suivies, 
volume total de circulations prévues, taux de retard et d'annulation du dernier mois disponible. 
La page propose également une évolution mensuelle des retards et des annulations, 
trois observations clés sur la tendance récente, le mois le plus perturbé et la principale cause de retard, 
ainsi qu'une répartition des causes et une visualisation de la saisonnalité.

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
La prévision s'appuie sur les taux de retard des trois derniers mois observés. 
La page affiche une carte interactive des gares de départ et d'arrivée, reliées par un tracé indicatif, ainsi que 
l'évolution historique des retards.
Elle présente également une évaluation du modèle sur des données historiques, avec une comparaison à une méthode de référence basée sur 
le taux de retard du mois précédent.