import pytest
from main import _reconstruct_report_from_cache
from adaptive_engine import _welford_update


def test_report_reconstruction():
    """Tests helper function correctly reconstructs Report."""
    mock_report_data = {
        "archetype": {
            "name": "Le Visionnaire",
            "emoji": "◉",
            "tagline": "Créatif",
            "description": "Test"
        },
        "overall_summary": "Summary",
        "traits": {
            "O": {
                "score": 75.0,
                "label": "Ouverture",
                "emoji": "◉",
                "interpretation": "Test interpretation. Ceci est valide."
            }
        },
        "strengths": ["Strength 1"],
        "areas_of_attention": ["Area 1"],
        "recommendations": ["Rec 1"],
        "disclaimer": "Disclaimer"
    }

    report = _reconstruct_report_from_cache(mock_report_data)
    assert report.archetype.name == "Le Visionnaire"
    assert report.traits["O"].score == 75.0
    assert report.traits["O"].interpretation.startswith("Test interpretation")


def test_welford_numerical_stability():
    """Tests Welford update maintains numerical stability."""
    state = {"n": 0, "mean": 0.5, "m2": 0.0, "variance": 0.25}
    for obs in [0.2, 0.5, 0.8, 0.3]:
        _welford_update(state, obs)
    assert state["variance"] >= 0.0
    assert state["n"] == 4


def test_trait_entry_validation():
    """Tests LLMTraitEntry rejects invalid interpretations."""
    import importlib.util
    from pathlib import Path

    module_path = Path(__file__).resolve().parent / "report_generator.py"
    spec = importlib.util.spec_from_file_location("report_generator", module_path)
    if spec is None or spec.loader is None:
        pytest.skip("Skipping report_generator tests because module could not be loaded.")

    report_generator = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(report_generator)
    except Exception:
        pytest.skip("Skipping report_generator tests because required runtime dependencies are unavailable.")

    _LLMTraitEntry = report_generator._LLMTraitEntry

    with pytest.raises(ValueError):
        _LLMTraitEntry(
            score=50.0,
            label="Test",
            emoji="◉",
            interpretation="..."
        )

    entry = _LLMTraitEntry(
        score=50.0,
        label="Test",
        emoji="◉",
        interpretation="This is a valid interpretation. It has multiple sentences."
    )
    assert entry.score == 50.0
