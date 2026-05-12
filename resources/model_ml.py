from sklearn.ensemble import RandomForestClassifier

def prepare_data(df):
    df = df.copy()

    # Target: sube más de 2% en 3 días
    df['future_return'] = df['Close'].shift(-3) / df['Close'] - 1
    df['target'] = (df['future_return'] > 0.008).astype(int)

    df = df.dropna()

    return df

def train_model(df, features):
    train = df[df.index < "2024-01-01"]
    test = df[df.index >= "2024-01-01"]

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        class_weight='balanced'
    )
    model.fit(train[features], train['target'])

    return model, train, test