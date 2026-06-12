from models.fusion_head import FusionHead


def test_fixed_attention_weights_are_deterministic() -> None:
    """Verify neural-only pipeline uses fixed deterministic attention weights."""
    head = FusionHead()
    text_w, visual_w, audio_w = head._fixed_attention_weights()

    # Fixed 60/20/20 split (text/visual/audio)
    assert text_w == 0.6
    assert visual_w == 0.2
    assert audio_w == 0.2
    assert abs((text_w + visual_w + audio_w) - 1.0) < 1e-6


def test_neural_infer_with_proper_dimensions() -> None:
    """Verify neural inference with proper embedding dimensions."""
    head = FusionHead()
    result = head.infer(
        text_embedding=[0.1] * 384,
        visual_embedding=[0.2] * 256,
        audio_embedding=[0.3] * 128,
    )

    attention = result["attention"]
    # Fixed attention weights
    assert abs(attention["text"] - 0.6) < 1e-6
    assert abs(attention["visual"] - 0.2) < 1e-6
    assert abs(attention["audio"] - 0.2) < 1e-6
    # Fused vector should have common dimension
    assert len(result["vector"]) == head.common_dim


def test_deterministic_fallback_fusion_returns_common_dim_vector() -> None:
    head = FusionHead()
    result = head._deterministic_fallback_fusion(
        text_embedding=[0.1] * 384,
        visual_embedding=[0.2] * 256,
        audio_embedding=[0.3] * 128,
    )

    assert len(result["vector"]) == head.common_dim
    assert set(result["attention"].keys()) == {"text", "visual", "audio"}
