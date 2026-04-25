import numpy as np
from src.regression import LinearRegressionScratch


def test_regression_fit_predict():
    X = np.array([[1], [2], [3], [4]])
    y = np.array([2, 4, 6, 8])

    model = LinearRegressionScratch(
        learning_rate=0.01,
        n_iterations=1000,
        verbose=0,
    )

    model.fit(X, y)
    pred = model.predict(np.array([[5]]))

    assert pred[0] > 8