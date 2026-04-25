from src.cleaner import AirbnbCleaner


def test_clean_price():
    cleaner = AirbnbCleaner()
    assert cleaner.clean_price("279 €") == "279 €"


def test_to_float_price():
    cleaner = AirbnbCleaner()
    assert cleaner.to_float_price("279 €") == 279.0


def test_new_listing():
    cleaner = AirbnbCleaner()
    assert cleaner.is_new_listing("Nouveau") is True