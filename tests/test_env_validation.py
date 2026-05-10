from src.core.config import Settings

def test_settings_loads_required_keys():
    settings = Settings()
    assert settings.anthropic_api_key, "ANTHROPIC_API_KEY missing"
    assert settings.elevenlabs_api_key, "ELEVENLABS_API_KEY missing"
    assert settings.elevenlabs_voice, "ELEVENLABS_VOICE missing"
    assert settings.pexels_api_key, "PEXELS_API_KEY missing"
    assert settings.dry_run is True, "Phase 1 must dry-run by default"
