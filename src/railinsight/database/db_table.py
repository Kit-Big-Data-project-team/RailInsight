from sqlalchemy import Column, Date, Integer, MetaData, Numeric, String, Table, UniqueConstraint

TABLE_NAME = "regularite_tgv"
KEY = [
    "date",
    "service",
    "gare_depart",
    "gare_arrivee",
]
metadata = MetaData()

# Table schema
regularite_tgv_table = Table(
    TABLE_NAME,
    metadata,
    Column("date", Date, nullable=False),
    Column("service", String(100), nullable=False),
    Column("gare_depart", String(255), nullable=False),
    Column("gare_arrivee", String(255), nullable=False),
    Column("duree_moyenne", Numeric(12, 2)),
    Column("nb_train_prevu", Integer),
    Column("nb_annulation", Integer),
    Column("nb_train_depart_retard", Integer),
    Column("retard_moyen_depart", Numeric(12, 2)),
    Column("retard_moyen_tous_trains_depart", Numeric(12, 2)),
    Column("nb_train_retard_arrivee", Integer),
    Column("retard_moyen_arrivee", Numeric(12, 2)),
    Column("retard_moyen_tous_trains_arrivee", Numeric(12, 2)),
    Column("nb_train_retard_sup_15", Integer),
    Column("retard_moyen_trains_retard_sup15", Numeric(12, 2)),
    Column("nb_train_retard_sup_30", Integer),
    Column("nb_train_retard_sup_60", Integer),
    Column("prct_cause_externe", Numeric(5, 2)),
    Column("prct_cause_infra", Numeric(5, 2)),
    Column("prct_cause_gestion_trafic", Numeric(5, 2)),
    Column("prct_cause_materiel_roulant", Numeric(5, 2)),
    Column("prct_cause_gestion_gare", Numeric(5, 2)),
    Column("prct_cause_prise_en_charge_voyageurs", Numeric(5, 2)),
    UniqueConstraint(*KEY, name="uq_regularite_tgv_date_service_gares"),
)
