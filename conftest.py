import pytest


@pytest.fixture
def cleaned_data():
    from analyzer.processor import clean_svo

    text = " ".join([
        "Cattleya orchids require bright light and warm temperatures",
        "Phalaenopsis species grows well in humid conditions with filtered light",
        "Dendrobium hybrids need good drainage and regular watering",
        "Oncidium orchids grow rapidly with adequate water and nutrients",
    ])

    result = clean_svo(text)
    return result.get("cleaned_data", [])


@pytest.fixture
def analysis_results(cleaned_data):
    from analyzer.analyzer import analyze_svo

    if not cleaned_data:
        return {}

    return analyze_svo(cleaned_data)


@pytest.fixture
def svo_data(cleaned_data):
    return cleaned_data
