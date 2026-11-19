"""Positions indicatives des gares et destinations du jeu de données TGV."""

STATIONS = {
    "AIX EN PROVENCE TGV": (43.4552, 5.3172),
    "ANGERS SAINT LAUD": (47.4649, -0.5568),
    "ANGOULEME": (45.6530, 0.1640),
    "ANNECY": (45.9010, 6.1210),
    "ARRAS": (50.2868, 2.7817),
    "AVIGNON TGV": (43.9217, 4.7860),
    "BARCELONA": (41.3790, 2.1400),
    "BELLEGARDE (AIN)": (46.1090, 5.8230),
    "BESANCON FRANCHE COMTE TGV": (47.3070, 5.9540),
    "BORDEAUX ST JEAN": (44.8258, -0.5560),
    "BREST": (48.3878, -4.4790),
    "CHAMBERY CHALLES LES EAUX": (45.5710, 5.9190),
    "DIJON VILLE": (47.3230, 5.0270),
    "DOUAI": (50.3710, 3.0900),
    "DUNKERQUE": (51.0310, 2.3680),
    "FRANCFORT": (50.1070, 8.6630),
    "GENEVE": (46.2100, 6.1420),
    "GRENOBLE": (45.1910, 5.7150),
    "ITALIE": (45.0703, 7.6869),
    "LA ROCHELLE VILLE": (46.1527, -1.1450),
    "LAUSANNE": (46.5170, 6.6290),
    "LAVAL": (48.0760, -0.7610),
    "LE CREUSOT MONTCEAU MONTCHANIN": (46.7650, 4.5000),
    "LE MANS": (47.9950, 0.1920),
    "LILLE": (50.6360, 3.0710),
    "LYON PART DIEU": (45.7606, 4.8595),
    "MACON LOCHE": (46.2820, 4.7790),
    "MADRID": (40.4060, -3.6900),
    "MARNE LA VALLEE": (48.8700, 2.7830),
    "MARSEILLE ST CHARLES": (43.3026, 5.3804),
    "METZ": (49.1090, 6.1770),
    "MONTPELLIER": (43.6040, 3.8810),
    "MULHOUSE VILLE": (47.7420, 7.3430),
    "NANCY": (48.6890, 6.1750),
    "NANTES": (47.2170, -1.5420),
    "NICE VILLE": (43.7050, 7.2620),
    "NIMES": (43.8320, 4.3660),
    "PARIS EST": (48.8760, 2.3590),
    "PARIS LYON": (48.8449, 2.3735),
    "PARIS MONTPARNASSE": (48.8410, 2.3200),
    "PARIS NORD": (48.8809, 2.3553),
    "PARIS VAUGIRARD": (48.8390, 2.3150),
    "PERPIGNAN": (42.6960, 2.8800),
    "POITIERS": (46.5820, 0.3330),
    "QUIMPER": (47.9940, -4.0930),
    "REIMS": (49.2590, 4.0240),
    "RENNES": (48.1040, -1.6720),
    "SAINT ETIENNE CHATEAUCREUX": (45.4430, 4.3990),
    "ST MALO": (48.6460, -2.0050),
    "ST PIERRE DES CORPS": (47.3860, 0.7230),
    "STRASBOURG": (48.5850, 7.7350),
    "STUTTGART": (48.7840, 9.1830),
    "TOULON": (43.1280, 5.9290),
    "TOULOUSE MATABIAU": (43.6110, 1.4540),
    "TOURCOING": (50.7160, 3.1680),
    "TOURS": (47.3890, 0.6940),
    "VALENCE ALIXAN TGV": (44.9920, 4.9780),
    "VANNES": (47.6650, -2.7520),
    "ZURICH": (47.3780, 8.5400),
}


def get_station_coordinates(name: str) -> tuple[float, float] | None:
    """Retourne la position indicative d'une gare ou destination.

    Args:
        name: Nom de la gare dans le jeu de données RailInsight.

    Returns:
        Couple (latitude, longitude), ou None si le nom est inconnu.
    """
    return STATIONS.get(name.strip().upper())
