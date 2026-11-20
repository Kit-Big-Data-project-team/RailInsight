"""Page Streamlit : fiabilité de la prévision (intervalles, backtesting, calibration).

Prolonge la prédiction ponctuelle par une évaluation honnête : une fourchette
d'incertitude autour de chaque prévision, une robustesse mesurée mois par mois
(backtesting glissant) et une vérification que l'intervalle est bien calibré.
"""

import logging

import pandas as pd
import streamlit as st

from railinsight.analysis.backtest import backtest_summary, walk_forward_backtest
from railinsight.analysis.forecast import get_recent_rates
from railinsight.analysis.forecast_intervals import fit_quantile_models, interval_coverage, predict_with_interval
from railinsight.analysis.prepare_prediction import monthly_rate_table, prepare_prediction_data
from railinsight.data.loader import TGVDataset
from railinsight.viz.forecast_intervals import backtest_error_line, forecast_interval_chart

logger = logging.getLogger(__name__)

# Durée de vie du cache : la base est rafraîchie une fois par mois, on évite de
# servir indéfiniment un instantané obsolète après une mise à jour.
CACHE_TTL = 3600


@st.cache_data(show_spinner="Évaluation de la fiabilité de la prévision...", ttl=CACHE_TTL)
def load():
    """Prépare les données, rejoue le backtesting, mesure la calibration et entraîne les quantiles."""
    raw = TGVDataset.from_db().df
    df = prepare_prediction_data(raw)
    monthly = monthly_rate_table(raw)
    backtest = walk_forward_backtest(df, n_months=12)
    summary = backtest_summary(backtest)
    coverage = interval_coverage(df)
    models = fit_quantile_models(df)
    reference = monthly["date"].max().to_period("M")
    return df, monthly, backtest, summary, coverage, models, reference


def liaison_forecast(monthly: pd.DataFrame, models: dict, liaison: str, reference: pd.Period):
    """Prévision du mois suivant la **référence globale**, avec intervalle, pour une liaison.

    Le mois prévu est ``reference + 1`` (dernier mois disponible dans tout le jeu de
    données), jamais le lendemain de la dernière observation propre à la liaison : une
    liaison dont les données s'arrêtent il y a des années ne doit pas afficher un mois
    passé comme s'il s'agissait d'une prévision future. Les taux récents proviennent de
    la série mensuelle complète, ce qui permet de prévoir même une liaison ne comptant
    que trois mois consécutifs. Une liaison sans trois mois consécutifs jusqu'à la
    référence est déclarée indisponible.
    """
    next_month = (reference + 1).to_timestamp()
    for service in sorted(monthly.loc[monthly["liaison"] == liaison, "service"].unique()):
        group = monthly[(monthly["liaison"] == liaison) & (monthly["service"] == service)].sort_values("date")
        rates = get_recent_rates(group, reference)
        if rates is None:
            continue
        features = pd.DataFrame(
            [{"late_rate_lag1": rates[2], "late_rate_lag2": rates[1], "late_rate_lag3": rates[0], "late_rate_mean3": sum(rates) / 3, "month": next_month.month}]
        )
        bounds = predict_with_interval(models, features).iloc[0]
        history = group[["date", "late_rate"]].tail(12)
        return history, {"date": next_month, "low": bounds["low"], "median": bounds["median"], "high": bounds["high"], "service": service}
    return None, None


def pct(value) -> str:
    """Formate une fraction en pourcentage, ou un tiret si indisponible."""
    return "—" if value is None or pd.isna(value) else f"{value:.1%}"


st.title("Fiabilité de la prévision")
st.write(
    "Une prévision n'a de valeur que si l'on sait **à quel point lui faire confiance**. Cette page "
    "encadre chaque prévision d'une **fourchette d'incertitude**, mesure la robustesse du modèle "
    "**mois par mois** (backtesting) et vérifie que l'incertitude annoncée est **honnête** (calibration)."
)

try:
    df, monthly, backtest, summary, coverage, models, reference = load()
except Exception:
    logger.exception("Impossible de charger les données de la fiabilité de la prévision.")
    st.error("Les données sont momentanément indisponibles. Réessayez ultérieurement.")
    st.stop()

st.subheader("Robustesse : backtesting glissant")
st.caption(
    "Pour chacun des 12 derniers mois, le modèle est réentraîné sur tout l'historique antérieur "
    "puis évalué sur ce mois. Aucune donnée future ne sert à l'entraînement."
)
if backtest.empty:
    st.info("Pas assez d'historique pour le backtesting.")
else:
    st.plotly_chart(backtest_error_line(backtest), use_container_width=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Erreur moyenne du modèle", pct(summary["mae_model"]))
    c2.metric("Erreur de la référence", pct(summary["mae_baseline"]))
    c3.metric("Mois évalués", summary["n_months"])
    if summary["mae_model"] is not None and summary["mae_baseline"] is not None:
        verdict = "bat la référence" if summary["mae_model"] < summary["mae_baseline"] else "ne dépasse pas la référence"
        st.caption(f"Sur ces mois, le modèle **{verdict}** (« reprendre le taux du mois précédent »).")

st.subheader("Honnêteté de l'incertitude : calibration")
st.caption("Un intervalle à 80 % bien calibré doit contenir environ 80 % des vraies valeurs sur une période de test.")
cov = coverage["coverage"]
col = st.columns(2)
col[0].metric("Couverture observée de l'intervalle 80 %", pct(cov))
col[1].metric("Cible", f"{coverage['target']:.0%}")
if cov is not None:
    if cov >= 0.75:
        st.success("L'intervalle est bien calibré : l'incertitude annoncée est honnête.")
    else:
        st.warning("L'intervalle est trop étroit (modèle trop confiant) : à élargir pour une incertitude honnête.")

st.subheader("Prévision du mois prochain, avec fourchette")
liaison = st.sidebar.selectbox("Liaison", sorted(monthly["liaison"].unique()))
history, forecast = liaison_forecast(monthly, models, liaison, reference)
if forecast is None:
    st.info("Pas de trois mois consécutifs récents pour cette liaison : prévision indisponible.")
else:
    st.plotly_chart(forecast_interval_chart(history, forecast), use_container_width=True)
    st.write(
        f"Prévision pour **{forecast['date']:%m/%Y}** ({forecast['service']}) : "
        f"**{forecast['median']:.1%}** de taux de retard, fourchette probable **{forecast['low']:.1%} – {forecast['high']:.1%}**."
    )
    st.caption("La fourchette (intervalle à 80 %) décrit l'incertitude de la prévision ; ce n'est pas une garantie sur votre prochain train.")
