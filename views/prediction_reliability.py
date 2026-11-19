"""Page Streamlit : fiabilité de la prévision (intervalles, backtesting, calibration).

Prolonge la prédiction ponctuelle par une évaluation honnête : une fourchette
d'incertitude autour de chaque prévision, une robustesse mesurée mois par mois
(backtesting glissant) et une vérification que l'intervalle est bien calibré.
"""

import pandas as pd
import streamlit as st

from railinsight.analysis.backtest import backtest_summary, walk_forward_backtest
from railinsight.analysis.forecast import get_recent_rates
from railinsight.analysis.forecast_intervals import fit_quantile_models, interval_coverage, predict_with_interval
from railinsight.analysis.prepare_prediction import prepare_prediction_data
from railinsight.viz.forecast_intervals import backtest_error_line, forecast_interval_chart


@st.cache_data(show_spinner="Évaluation de la fiabilité de la prévision...")
def load():
    """Prépare les données, rejoue le backtesting, mesure la calibration et entraîne les quantiles."""
    df = prepare_prediction_data()
    backtest = walk_forward_backtest(df, n_months=12)
    summary = backtest_summary(backtest)
    coverage = interval_coverage(df)
    models = fit_quantile_models(df)
    return df, backtest, summary, coverage, models


def liaison_forecast(df: pd.DataFrame, models: dict, liaison: str):
    """Prévision du mois prochain avec intervalle pour une liaison (premier service exploitable)."""
    for service in sorted(df.loc[df["liaison"] == liaison, "service"].unique()):
        group = df[(df["liaison"] == liaison) & (df["service"] == service)].sort_values("date")
        latest = group["date"].max().to_period("M")
        rates = get_recent_rates(group, latest)
        if rates is None:
            continue
        next_month = (latest + 1).to_timestamp()
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

df, backtest, summary, coverage, models = load()

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
liaison = st.sidebar.selectbox("Liaison", sorted(df["liaison"].unique()))
history, forecast = liaison_forecast(df, models, liaison)
if forecast is None:
    st.info("Pas de trois mois consécutifs récents pour cette liaison : prévision indisponible.")
else:
    st.plotly_chart(forecast_interval_chart(history, forecast), use_container_width=True)
    st.write(
        f"Prévision pour **{forecast['date']:%m/%Y}** ({forecast['service']}) : "
        f"**{forecast['median']:.1%}** de taux de retard, fourchette probable **{forecast['low']:.1%} – {forecast['high']:.1%}**."
    )
    st.caption("La fourchette (intervalle à 80 %) décrit l'incertitude de la prévision ; ce n'est pas une garantie sur votre prochain train.")
