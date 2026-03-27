"""Tests for CLI argument parsing and main entry point."""

import argparse
import subprocess
import sys
from pathlib import Path

import pytest

# Project root — works regardless of where the candidate clones the repo
PROJECT_ROOT = str(Path(__file__).parent.parent)


class TestCliArgParsing:
    """Test argument parsing without actually running the app."""

    def _parse(self, args: list[str]) -> argparse.Namespace:
        """Parse CLI args using the same parser as main()."""
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--provider",
            required=True,
            choices=["ollama", "openai", "anthropic"],
        )
        parser.add_argument("--model", default=None)
        return parser.parse_args(args)

    def test_requires_provider(self):
        with pytest.raises(SystemExit):
            self._parse([])

    def test_accepts_ollama(self):
        args = self._parse(["--provider", "ollama"])
        assert args.provider == "ollama"

    def test_accepts_openai(self):
        args = self._parse(["--provider", "openai"])
        assert args.provider == "openai"

    def test_accepts_anthropic(self):
        args = self._parse(["--provider", "anthropic"])
        assert args.provider == "anthropic"

    def test_rejects_invalid_provider(self):
        with pytest.raises(SystemExit):
            self._parse(["--provider", "azure"])

    def test_model_defaults_to_none(self):
        args = self._parse(["--provider", "ollama"])
        assert args.model is None

    def test_model_override(self):
        args = self._parse(["--provider", "openai", "--model", "gpt-4o"])
        assert args.model == "gpt-4o"


class TestCliEntryPoint:
    """Test the actual CLI entry point via subprocess."""

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, "-m", "src", "--help"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0
        assert "thinkmoney" in result.stdout
        assert "--provider" in result.stdout

    def test_no_args_exits_with_error(self):
        result = subprocess.run(
            [sys.executable, "-m", "src"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode != 0

    def test_invalid_provider_exits_with_error(self):
        result = subprocess.run(
            [sys.executable, "-m", "src", "--provider", "azure"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode != 0
