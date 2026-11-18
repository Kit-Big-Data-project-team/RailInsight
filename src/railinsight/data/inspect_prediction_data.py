
"""Inspecte les données disponibles pour préparer la prédiction des retards TGV."""

from railinsight.data.loader import TGVDataset


def main() -> None:
    """Charge les données et affiche les informations nécessaires à leur exploration."""

    # Chargement du dataset depuis PostgreSQL.
    dataset = TGVDataset.from_db()
    df = dataset.df.copy()

    print("\n===== 1. DIMENSIONS DU DATASET =====")
    print(f"Nombre de lignes : {df.shape[0]}")
    print(f"Nombre de colonnes : {df.shape[1]}")

    print("\n===== 2. COLONNES DISPONIBLES =====")
    print(df.columns.tolist())

    print("\n===== 3. TYPES DES COLONNES =====")
    print(df.dtypes)

    print("\n===== 4. PERIODE DISPONIBLE =====")
    print(f"Première date : {df['date'].min()}")
    print(f"Dernière date : {df['date'].max()}")
    print(f"Nombre de mois distincts : {df['date'].nunique()}")

    print("\n===== 5. NOMBRE DE LIAISONS =====")
    print(f"Nombre de liaisons : {df['liaison'].nunique()}")

    print("\n===== 6. HISTORIQUE PAR LIAISON =====")
    months_per_liaison = df.groupby("liaison")["date"].nunique()

    print(months_per_liaison.describe())

    print("\nLes 10 liaisons ayant le moins de mois disponibles :")
    print(months_per_liaison.sort_values().head(10))

    print("\nLes 10 liaisons ayant le plus de mois disponibles :")
    print(months_per_liaison.sort_values(ascending=False).head(10))

    print("\n===== 7. VALEURS MANQUANTES =====")
    print(df.isna().sum())

    print("\n===== 8. DOUBLONS LIAISON-MOIS =====")
    duplicates = df.duplicated(subset=["date", "liaison"]).sum()
    print(f"Nombre de doublons : {duplicates}")

    print("\n===== 9. VARIABLES NECESSAIRES A LA PREDICTION =====")

    required_columns = [
        "date",
        "liaison",
        "scheduled",
        "cancelled",
        "late_arrival",
        "avg_delay_arrival",
    ]

    for column in required_columns:
        print(f"{column} : {'Disponible' if column in df.columns else 'Absente'}")

    print("\n===== VERIFICATIONS AVANT PREDICTION =====")
    # 1. Doublons selon la véritable clé métier
    nb_doublons = df.duplicated(
    subset=["date", "service", "origin", "destination"]
    ).sum()

    print("Doublons sur la clé métier :", nb_doublons)
    
    # 2. Vérifier les liaisons présentes dans plusieurs services
    print("\nLiaisons avec plusieurs services :")
    print(
    df.groupby("liaison")["service"]
    .nunique()
    .loc[lambda x: x > 1]
    .head(10)
    )

    # 3. Vérifier les circulations nulles
    print("\nLignes avec zéro circulation prévue :")
    print((df["scheduled"] == 0).sum())   

    # 4. Vérifier la cohérence des nombres de trains
    print("\nLignes avec annulations > circulations prévues :")
    print((df["cancelled"] > df["scheduled"]).sum())


if __name__ == "__main__":
    main()
