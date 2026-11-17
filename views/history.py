"""
Description :
Page Historique & évolution (tâche 4) : évolution des retards et des annulations
dans le temps, répartition par cause et saisonnalité, pour les liaisons disponibles ou une liaison.
"""

import logging

import pandas as pd
import streamlit as st

from railinsight.analysis.history import (
    CAUSE_COLUMNS,
    cause_breakdown_over_time,
    delay_severity_over_time,
    history_cause_observations,
    history_period_summary,
    history_trend_observations,
    monthly_delays_cancellations,
    punctuality_by_service,
    seasonality,
    severity_source_issues,
)
from railinsight.data.loader import TGVDataset
from railinsight.exceptions import RailInsightError
from railinsight.viz.history import CAUSE_LABELS, MONTH_LABELS, cause_area, delays_cancellations_line, seasonality_bar, service_line, severity_area

logger = logging.getLogger(__name__)


@st.cache_data
def load() -> TGVDataset:
    """Charge les données partagées depuis PostgreSQL et met le résultat en cache."""
    return TGVDataset.from_db()


st.title("Historique & évolution des retards")
st.write(
    "Évolution des retards et des annulations dans le temps, répartition par cause " "et saisonnalité. Choisissez une liaison dans le menu, ou consultez toutes les liaisons disponibles."
)

ds = load()
options = ["Toutes les liaisons disponibles"] + ds.routes()
choix = st.sidebar.selectbox("Liaison", options)

try:
    data = ds.df if choix == "Toutes les liaisons disponibles" else ds.for_route(choix)
    if data.empty:
        st.info("Aucune donnée disponible pour cette sélection.")
        st.stop()
    months = sorted(pd.to_datetime(data["date"]).unique())
    start, end = st.sidebar.select_slider(
        "Période",
        options=months,
        value=(months[0], months[-1]),
        format_func=lambda date: f"{MONTH_LABELS[pd.Timestamp(date).month]} {pd.Timestamp(date).year}",
    )
    dates = pd.to_datetime(data["date"])
    data = data.loc[dates.between(start, end)].copy()
    logger.info("Consultation de l'historique : liaison=%s, début=%s, fin=%s", choix, start, end)
    summary = history_period_summary(data)
    columns = st.columns(4)
    for column, key, label in zip(
        columns[:3], ("late_rate", "cancellation_rate", "disruption_rate"), ("Taux de retard sur la période", "Taux d'annulation sur la période", "Taux de perturbation sur la période")
    ):
        value = summary[key]
        column.metric(label, f"{value:.1%}" if value is not None else "—")
    columns[3].metric("Circulations prévues enregistrées", f"{summary['scheduled']:,}".replace(",", " "))

    if choix == "Toutes les liaisons disponibles":
        st.info(
            "Ces indicateurs regroupent les enregistrements des liaisons disponibles. "
            "Un même TGV peut figurer dans plusieurs liaisons : ces résultats ne constituent "
            "donc pas les taux officiels du réseau TGV et ne comptent pas nécessairement "
            "chaque train une seule fois."
        )
    st.caption("Source et limites : [SNCF — Régularité mensuelle TGV par liaisons]" "(https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/information/).")

    st.subheader("Retards, annulations et perturbations dans le temps")
    st.caption(
        "Retards : trains arrivés en retard / trains ayant circulé. "
        "Annulations : trains annulés / trains prévus. "
        "Perturbations : (trains annulés + trains arrivés en retard) / trains prévus. "
        "Les trois courbes ne s'additionnent pas : les dénominateurs diffèrent. "
        "Un taux non calculable est laissé manquant."
    )
    st.plotly_chart(delays_cancellations_line(monthly_delays_cancellations(data)), width="stretch")
    observations = history_trend_observations(data)
    st.markdown("**À retenir pour cette sélection**")
    peak_rate = observations["peak_disruption_rate"]
    peaks = observations["peak_months"]
    if peak_rate is None:
        st.write("Les taux mensuels de perturbation sont indisponibles : aucun maximum ne peut être déterminé.")
    elif observations["disrupted_count"] == 0:
        st.write("Aucun retard ni aucune annulation n'est enregistré dans cette sélection.")
    elif observations["constant_rate"]:
        value = f"{peak_rate:.1%}".replace(".", ",")
        st.write(f"Le taux de perturbation est identique dans les {observations['n_valid_months']} mois calculables : {value}.")
    elif len(peaks) == 1:
        peak = peaks.iloc[0]
        date = pd.Timestamp(peak["date"])
        value = f"{peak_rate:.1%}".replace(".", ",")
        st.write(
            f"Le taux de perturbation le plus élevé de la sélection est observé en {MONTH_LABELS[date.month]} {date.year} : {value}, "
            f"pour {int(peak['scheduled'])} circulations prévues enregistrées "
            f"({int(peak['cancelled'])} annulations et {int(peak['late_arrival'])} arrivées en retard)."
        )
    else:
        dates = [pd.Timestamp(date) for date in peaks["date"]]
        names = ", ".join(f"{MONTH_LABELS[date.month]} {date.year}" for date in dates[:3])
        remainder = f", et {len(dates) - 3} autre(s) mois" if len(dates) > 3 else ""
        value = f"{peak_rate:.1%}".replace(".", ",")
        st.write(f"Le maximum de perturbation ({value}) est partagé par {len(dates)} mois : {names}{remainder}.")
    if observations["cancelled_share"] is not None:
        cancelled = f"{observations['cancelled_share']:.1%}".replace(".", ",")
        late = f"{observations['late_share']:.1%}".replace(".", ",")
        st.write(
            f"Sur la période sélectionnée, parmi les perturbations enregistrées, {cancelled} correspondent à des annulations "
            f"et {late} à des arrivées en retard. Ces parts décrivent les effectifs et non la gravité des conséquences."
        )
    if observations["n_valid_months"] < observations["n_months"]:
        st.caption("Les mois dont le taux est indisponible ne participent pas à la recherche du maximum.")
    if observations["n_months"] == 1:
        st.caption("Un seul mois est sélectionné : aucune évolution dans le temps ne peut être déduite.")

    st.subheader("Comparaison des services")
    services = punctuality_by_service(data)
    if services.empty:
        st.info("La comparaison des services n'est pas disponible pour cette sélection.")
    else:
        if services["service"].nunique() < 2:
            st.caption("Un seul service est présent : aucune comparaison entre services n'est possible.")
        st.plotly_chart(service_line(services), width="stretch")
        st.caption("Les différences observées peuvent refléter des liaisons et durées différentes ; elles ne démontrent pas un effet causal du type de service.")

    st.subheader("Sévérité des retards")
    severity = delay_severity_over_time(data)
    issues = severity_source_issues(data)
    if not issues.empty:
        st.caption("Certaines données de retard sont incohérentes dans la source. Les résultats concernés ne sont pas affichés.")
    st.plotly_chart(severity_area(severity), width="stretch")
    st.caption(
        "Parts rapportées aux circulations prévues enregistrées. Les seuils sont cumulatifs : ils ne s'additionnent pas. "
        "Le champ > 15 min est documenté par la SNCF avec la réserve « si liaison concurrencée par vol » ; "
        "son périmètre d'application reste à confirmer. Une coupure indique un résultat indisponible."
    )

    st.subheader("Répartition des causes de retard")
    st.caption(
        "Les six causes sont celles déclarées dans les données et concernent les retards, pas les annulations. "
        "Hypothèse de calcul : pondération par le nombre de trains en retard à l'arrivée ; "
        "ce dénominateur n'est pas explicitement confirmé par les métadonnées SNCF. "
        "La part grise complète la répartition lorsqu'elle est incomplète : elle représente une part non ventilée, "
        "pas une cause identifiée. Les pourcentages déclarés ne sont pas renormalisés. "
        "Un écart inférieur ou égal à 0,1 point de pourcentage est toléré pour les arrondis."
    )
    causes = cause_breakdown_over_time(data)
    if causes.empty:
        st.info("Aucune donnée disponible pour les causes de retard.")
    elif causes[CAUSE_COLUMNS].isna().all().all():
        st.info("Aucun retard enregistré sur la période : aucune répartition des causes à afficher.")
    else:
        st.plotly_chart(cause_area(causes), width="stretch")
        cause_observations = history_cause_observations(data)
        leaders = cause_observations["leaders"]
        if leaders:
            names = ", ".join(CAUSE_LABELS[cause] for cause in leaders)
            value = f"{cause_observations['largest_reported_share']:.1f}".replace(".", ",")
            qualifier = "La part déclarée la plus élevée est" if len(leaders) == 1 else "Les parts déclarées les plus élevées sont ex aequo"
            st.write(f"{qualifier} : {names} ({value} % pour chaque catégorie citée, sur la période sélectionnée et selon la pondération indiquée).")
        else:
            st.write("Aucune cause n'est ventilée dans les données de cette sélection, malgré la présence de retards.")
        value = f"{cause_observations['unallocated_share']:.1f}".replace(".", ",")
        st.caption(f"Part non ventilée sur la période : {value} %. Les informations disponibles ne permettent pas d'attribuer cette part à une cause.")

    st.subheader("Comparaison par mois de l'année")
    seasonal = seasonality(data)
    st.caption(
        "Seules les années comportant les douze mois dans la sélection courante sont retenues. "
        "Les effectifs sont regroupés avant le calcul des taux : les années de fort trafic contribuent davantage. "
        "Les années exceptionnelles, dont 2020, restent incluses. Cette comparaison descriptive ne démontre pas un effet saisonnier récurrent."
    )
    if seasonal.empty:
        st.info("Aucune année complète dans la sélection : élargissez la période pour comparer les mois de l'année.")
    else:
        st.plotly_chart(seasonality_bar(seasonal), width="stretch")
        st.caption(f"Chaque mois repose sur {int(seasonal['n_years'].min())} année(s) complète(s). Les taux ont des dénominateurs différents et ne s'additionnent pas.")
except RailInsightError as e:  # erreurs métier → message propre, pas de traceback
    st.error(f"Impossible d'afficher ces données : {e}")
