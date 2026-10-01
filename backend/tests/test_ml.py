from app.ml import EcosystemAutoencoder


def test_neural_reconstruction_model_learns_normal_pattern():
    rows = [
        [0.10,0.12,0.08,0.10],[0.12,0.11,0.10,0.12],[0.09,0.14,0.09,0.11],
        [0.11,0.13,0.12,0.10],[0.13,0.12,0.10,0.13],[0.10,0.11,0.09,0.12],
        [0.12,0.13,0.11,0.11],[0.09,0.12,0.10,0.09],
    ]
    model = EcosystemAutoencoder().fit(rows)
    normal = model.score([0.11,0.12,0.10,0.11])
    unusual = model.score([0.95,0.90,0.88,0.94])
    assert 0 <= normal <= 1
    assert 0 <= unusual <= 1
    assert unusual >= normal
