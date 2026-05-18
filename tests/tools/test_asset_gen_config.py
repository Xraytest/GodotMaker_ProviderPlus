"""Tests for asset_gen.py project config handling."""
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "tools",
))

import asset_gen


def _args(**overrides):
    base = {
        "model": None,
        "size": "1K",
        "aspect_ratio": "1:1",
        "image": None,
        "prompt": "a yellow banana icon",
        "output": "assets/img/out.png",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _unexpected_call(*_args, **_kwargs):
    pytest.fail("unexpected backend call")


def test_load_project_config_reads_top_level_scalars(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / ".godotmaker" / "config.yaml"
    config.parent.mkdir()
    config.write_text(
        "asset_image_model: gemini:gemini-3.1-flash-image-preview # comment\n"
        "nested:\n"
        "  ignored: value\n",
        encoding="utf-8",
    )

    assert asset_gen._load_project_config()["asset_image_model"] == (
        "gemini:gemini-3.1-flash-image-preview"
    )
    assert "ignored" not in asset_gen._load_project_config()


def test_image_without_api_selector_exits_with_runtime_message(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(asset_gen, "_generate_gemini", _unexpected_call)
    monkeypatch.setattr(asset_gen, "_generate_grok", _unexpected_call)
    monkeypatch.setattr(asset_gen, "_generate_openai", _unexpected_call)

    with pytest.raises(SystemExit):
        asset_gen.cmd_image(_args())

    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False
    assert "asset_image_model: native" in out["error"]


def test_cli_gemini_alias_uses_default_gemini_model(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    seen = {}

    def fake_gemini(args, output, cost, model_name):
        seen.update({"output": output, "cost": cost, "model": model_name})

    monkeypatch.setattr(asset_gen, "_generate_gemini", fake_gemini)
    monkeypatch.setattr(asset_gen, "_generate_grok", _unexpected_call)

    asset_gen.cmd_image(_args(model="gemini"))

    assert seen == {
        "output": Path("assets/img/out.png"),
        "cost": 7,
        "model": "gemini-3.1-flash-image-preview",
    }


def test_project_config_can_select_grok_and_model(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / ".godotmaker" / "config.yaml"
    config.parent.mkdir()
    config.write_text("asset_image_model: grok:custom-grok-image\n", encoding="utf-8")
    seen = {}

    def fake_grok(args, output, cost, model_name):
        seen.update({"cost": cost, "model": model_name})

    monkeypatch.setattr(asset_gen, "_generate_gemini", _unexpected_call)
    monkeypatch.setattr(asset_gen, "_generate_grok", fake_grok)

    asset_gen.cmd_image(_args())

    assert seen == {"cost": 2, "model": "custom-grok-image"}


def test_cli_model_override_wins_over_project_provider(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / ".godotmaker" / "config.yaml"
    config.parent.mkdir()
    config.write_text("asset_image_model: grok:grok-imagine-image\n", encoding="utf-8")
    seen = {}

    def fake_gemini(args, output, cost, model_name):
        seen["model"] = model_name

    monkeypatch.setattr(asset_gen, "_generate_gemini", fake_gemini)
    monkeypatch.setattr(asset_gen, "_generate_grok", _unexpected_call)

    asset_gen.cmd_image(_args(model="gemini"))

    assert seen == {"model": "gemini-3.1-flash-image-preview"}


def test_invalid_project_provider_exits_with_json_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / ".godotmaker" / "config.yaml"
    config.parent.mkdir()
    config.write_text("asset_image_model: nope\n", encoding="utf-8")

    with pytest.raises(SystemExit):
        asset_gen.cmd_image(_args())

    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False
    assert "Invalid asset_image_model" in out["error"]


def test_project_config_can_select_openai_and_model(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / ".godotmaker" / "config.yaml"
    config.parent.mkdir()
    config.write_text("asset_image_model: openai:gpt-image-1-mini\n", encoding="utf-8")
    seen = {}

    def fake_openai(args, output, cost, model_name):
        seen.update({"cost": cost, "model": model_name, "output": output})

    monkeypatch.setattr(asset_gen, "_generate_gemini", _unexpected_call)
    monkeypatch.setattr(asset_gen, "_generate_grok", _unexpected_call)
    monkeypatch.setattr(asset_gen, "_generate_openai", fake_openai)

    asset_gen.cmd_image(_args())

    assert seen == {
        "cost": 5,
        "model": "gpt-image-1-mini",
        "output": Path("assets/img/out.png"),
    }


def test_cli_openai_alias_uses_default_openai_model(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    seen = {}

    def fake_openai(args, output, cost, model_name):
        seen.update({"cost": cost, "model": model_name, "output": output})

    monkeypatch.setattr(asset_gen, "_generate_gemini", _unexpected_call)
    monkeypatch.setattr(asset_gen, "_generate_grok", _unexpected_call)
    monkeypatch.setattr(asset_gen, "_generate_openai", fake_openai)

    asset_gen.cmd_image(_args(model="openai"))

    assert seen == {
        "cost": 5,
        "model": "gpt-image-2",
        "output": Path("assets/img/out.png"),
    }


def test_native_image_model_exits_with_runtime_message(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / ".godotmaker" / "config.yaml"
    config.parent.mkdir()
    config.write_text("asset_image_model: native\n", encoding="utf-8")

    with pytest.raises(SystemExit):
        asset_gen.cmd_image(_args())

    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False
    assert "agent runtime" in out["error"]


def test_codex_image_model_exits_with_runtime_message(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / ".godotmaker" / "config.yaml"
    config.parent.mkdir()
    config.write_text("asset_image_model: codex\n", encoding="utf-8")

    with pytest.raises(SystemExit):
        asset_gen.cmd_image(_args())

    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False
    assert "agent runtime" in out["error"]


def test_legacy_project_config_still_selects_grok(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / ".godotmaker" / "config.yaml"
    config.parent.mkdir()
    config.write_text(
        "asset_image_provider: grok\n"
        "grok_image_model: custom-grok-image\n",
        encoding="utf-8",
    )
    seen = {}

    def fake_grok(args, output, cost, model_name):
        seen.update({"cost": cost, "model": model_name})

    monkeypatch.setattr(asset_gen, "_generate_gemini", _unexpected_call)
    monkeypatch.setattr(asset_gen, "_generate_openai", _unexpected_call)
    monkeypatch.setattr(asset_gen, "_generate_grok", fake_grok)

    asset_gen.cmd_image(_args())

    assert seen == {"cost": 2, "model": "custom-grok-image"}


def test_none_video_model_exits_with_disabled_message(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / ".godotmaker" / "config.yaml"
    config.parent.mkdir()
    config.write_text("asset_video_model: none\n", encoding="utf-8")
    image = tmp_path / "reference.png"
    image.write_bytes(b"png")

    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "xai_sdk":
            raise ImportError("xai_sdk unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    with pytest.raises(SystemExit):
        asset_gen.cmd_video(SimpleNamespace(
            prompt="camera push in",
            image=str(image),
            duration=1,
            resolution="720p",
            output="assets/video/out.mp4",
        ))

    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False
    assert "asset_video_model is set to 'none'" in out["error"]
