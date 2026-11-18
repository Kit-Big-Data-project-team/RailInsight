"""Thème graphique commun à toutes les visualisations de RailInsight.

Importer ce module suffit : il enregistre un template Plotly nommé « railinsight »
et le définit comme thème par défaut de toutes les figures créées ensuite. Les
couleurs sont définies une seule fois ici, pour que chaque graphique, de la page
d'accueil à « Mon trajet », reste dans la même famille de bleus et de pastels.
"""

import plotly.graph_objects as go
import plotly.io as pio

# Bleus de base (titres, éléments principaux).
PRIMARY = "#2F5D8C"
PRIMARY_DARK = "#1F3F66"

# Textes, grilles et gris-bleu neutre (par exemple pour la part « non ventilée »).
TEXT = "#27364B"
MUTED = "#5F6F86"
GRID = "#E4EAF2"
NEUTRAL = "#B4BFCD"

FONT = "Source Sans Pro, Segoe UI, Helvetica, Arial, sans-serif"

# Palette qualitative : un bleu profond, puis des pastels (teal, bleu ciel,
# lavande, pêche, ardoise). L'ordre compte : les deux premières couleurs sont
# celles des graphiques à deux courbes et doivent bien se distinguer.
QUALITATIVE = [
    PRIMARY,
    "#6EC6C0",
    "#9DB7F0",
    "#B9A9E8",
    "#F4B9A8",
    "#8FA3BD",
]

# Palette séquentielle (heatmaps, échelles continues) : du bleu très pâle au bleu profond.
SEQUENTIAL = [
    [0.0, "#EEF4FB"],
    [0.2, "#CFE0F5"],
    [0.4, "#A4C4EA"],
    [0.6, "#6F9FD6"],
    [0.8, "#3F74B0"],
    [1.0, "#1F4A7A"],
]

# Une cause de retard garde la même couleur sur toutes les pages.
CAUSE_COLORS = {
    "Externe": QUALITATIVE[0],
    "Infrastructure": QUALITATIVE[1],
    "Gestion du trafic": QUALITATIVE[2],
    "Matériel roulant": QUALITATIVE[3],
    "Gestion en gare": QUALITATIVE[4],
    "Prise en charge voyageurs": QUALITATIVE[5],
    "Part non ventilée dans les données": NEUTRAL,
}

# Les trois issues possibles d'une circulation (page « Mon trajet »).
OUTCOME_COLORS = {
    "À l'heure selon les seuils SNCF": PRIMARY,
    "Arrivées en retard": "#9DB7F0",
    "Annulations": "#F4B9A8",
}

TEMPLATE_NAME = "railinsight"


def _build_template() -> go.layout.Template:
    """Construit le template Plotly : polices, grilles, légende et couleurs."""
    axis = dict(
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        linecolor=GRID,
        ticks="outside",
        tickcolor=GRID,
        ticklen=4,
        tickfont=dict(color=MUTED),
        title=dict(font=dict(color=MUTED)),
    )
    return go.layout.Template(
        layout=go.Layout(
            colorway=QUALITATIVE,
            font=dict(family=FONT, size=13, color=TEXT),
            title=dict(font=dict(size=18, color=PRIMARY_DARK), x=0, xanchor="left", y=0.98, yanchor="top", yref="container"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis={**axis, "showgrid": False},
            yaxis=axis,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(color=TEXT)),
            hoverlabel=dict(bgcolor="white", bordercolor=GRID, font=dict(color=TEXT)),
            colorscale=dict(sequential=SEQUENTIAL, sequentialminus=SEQUENTIAL),
            coloraxis=dict(colorbar=dict(outlinewidth=0, ticks="")),
            bargap=0.25,
            bargroupgap=0.06,
            margin=dict(l=12, r=12, t=110, b=12),
        ),
        data=dict(
            scatter=[go.Scatter(line=dict(width=3))],
            bar=[go.Bar(marker=dict(line=dict(width=0)))],
        ),
    )


# On garde les bases de « plotly_white » et on y superpose le thème RailInsight.
pio.templates[TEMPLATE_NAME] = _build_template()
pio.templates.default = f"plotly_white+{TEMPLATE_NAME}"
