from sklearn.ensemble import RandomForestClassifier


def prepare_data(df):
    """
    Prepara el DataFrame para entrenamiento.
    Target: subida >= 3% en 3 días (objetivo real del proyecto).
    """
    df = df.copy()
    df["future_return"] = df["Close"].shift(-3) / df["Close"] - 1
    df["target"]        = (df["future_return"] >= 0.03).astype(int)
    df = df.dropna()
    return df


def train_model(df, features):
    """
    Entrena un RandomForest con split temporal 80/20.
    Retorna: (model, train_df, test_df)
    """
    train = df[df.index < "2024-01-01"]
    test  = df[df.index >= "2024-01-01"]

    available = [f for f in features if f in df.columns]

    model = RandomForestClassifier(
        n_estimators=400,
        max_depth=12,
        min_samples_leaf=5,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(train[available], train["target"])

    return model, train, test
