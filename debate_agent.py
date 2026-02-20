from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
import yaml
from dotenv import load_dotenv
import os


@dataclass
class Debater:
    alias: str
    model: str
    language: str
    stance: str


@dataclass
class ObjectiveConfig:
    topic: str
    rounds: int
    speech_word_target: int
    research_rounds_per_debater: int
    debaters: list[Debater]
    speeches_dir: Path
    memory_dir: Path
    transcript_dir: Path
    transcript_file: str
    save_json_log: bool


class OpenRouterClient:
    def __init__(self) -> None:
        load_dotenv()
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.api_url = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
        self.site_url = os.getenv("OPENROUTER_SITE_URL", "")
        self.app_name = os.getenv("OPENROUTER_APP_NAME", "Agent for Debate Project")

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is missing. Create a .env file from .env.example.")

    def chat(self, model: str, system_prompt: str, user_prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.app_name:
            headers["X-Title"] = self.app_name

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        response = requests.post(self.api_url, headers=headers, json=payload, timeout=180)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


def parse_objective(path: Path) -> ObjectiveConfig:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"```yaml\s*(.*?)```", text, flags=re.DOTALL)
    if not match:
        raise ValueError("OBJECTIVE.md must include a fenced YAML block.")

    cfg: dict[str, Any] = yaml.safe_load(match.group(1))

    debaters = [
        Debater(
            alias=d["alias"],
            model=d["model"],
            language=d.get("language", "English"),
            stance=d.get("stance", ""),
        )
        for d in cfg["debaters"]
    ]

    output = cfg["output"]
    return ObjectiveConfig(
        topic=cfg["topic"],
        rounds=int(cfg["rounds"]),
        speech_word_target=int(cfg["speech_word_target"]),
        research_rounds_per_debater=int(cfg["research_rounds_per_debater"]),
        debaters=debaters,
        speeches_dir=Path(output["speeches_dir"]),
        memory_dir=Path(output["memory_dir"]),
        transcript_dir=Path(output["transcript_dir"]),
        transcript_file=output["transcript_file"],
        save_json_log=bool(output.get("save_json_log", False)),
    )


def ensure_dirs(config: ObjectiveConfig) -> None:
    config.speeches_dir.mkdir(parents=True, exist_ok=True)
    config.memory_dir.mkdir(parents=True, exist_ok=True)
    config.transcript_dir.mkdir(parents=True, exist_ok=True)
    for debater in config.debaters:
        (config.memory_dir / debater.alias).mkdir(parents=True, exist_ok=True)
    for round_num in range(1, config.rounds + 1):
        (config.speeches_dir / f"Round_{round_num}").mkdir(parents=True, exist_ok=True)


def run_research(client: OpenRouterClient, config: ObjectiveConfig, dry_run: bool = False) -> None:
    for debater in config.debaters:
        memory_folder = config.memory_dir / debater.alias
        for i in range(1, config.research_rounds_per_debater + 1):
            prompt = (
                f"Topic: {config.topic}\n"
                f"You are {debater.alias}. Your stance: {debater.stance}.\n"
                f"Write human-readable research notes (headings + bullets + short synthesis).\n"
                f"Language: {debater.language}.\n"
                "Focus on evidence, policy options, risks, and trade-offs."
            )
            if dry_run:
                content = f"[DRY RUN] Research notes for {debater.alias}, round {i}."
            else:
                content = client.chat(
                    model=debater.model,
                    system_prompt="You are a rigorous research assistant preparing pre-debate notes.",
                    user_prompt=prompt,
                )

            output_file = memory_folder / f"research_round_{i}.md"
            output_file.write_text(content + "\n", encoding="utf-8")


def collect_speech_history(config: ObjectiveConfig) -> str:
    items: list[str] = []
    for round_num in range(1, config.rounds + 1):
        round_path = config.speeches_dir / f"Round_{round_num}"
        if not round_path.exists():
            continue
        for speech_file in sorted(round_path.glob("Speaker_*_*.md")):
            items.append(f"## {speech_file.name}\n\n{speech_file.read_text(encoding='utf-8')}")
    return "\n\n".join(items)


def run_debate(client: OpenRouterClient, config: ObjectiveConfig, dry_run: bool = False) -> list[dict[str, Any]]:
    logs: list[dict[str, Any]] = []
    transcript_path = config.transcript_dir / config.transcript_file
    transcript_path.write_text(f"# Debate Transcript\n\nTopic: {config.topic}\n\n", encoding="utf-8")

    for round_num in range(1, config.rounds + 1):
        for idx, debater in enumerate(config.debaters, start=1):
            memory_notes = "\n\n".join(
                p.read_text(encoding="utf-8")
                for p in sorted((config.memory_dir / debater.alias).glob("*.md"))
            )
            history = collect_speech_history(config)

            prompt = (
                f"Debate topic: {config.topic}\n"
                f"Current round: {round_num}\n"
                f"You are debater {debater.alias}. Stance: {debater.stance}.\n"
                f"Target length: approximately {config.speech_word_target} words.\n"
                f"Language: {debater.language}.\n\n"
                "You may use your research notes and prior speeches.\n"
                "Provide a structured argument and directly engage with others where relevant.\n\n"
                f"Your research notes:\n{memory_notes}\n\n"
                f"Prior speeches:\n{history}"
            )

            if dry_run:
                speech = (
                    f"[DRY RUN] Round {round_num} speech by {debater.alias}. "
                    f"Topic: {config.topic}."
                )
            else:
                speech = client.chat(
                    model=debater.model,
                    system_prompt="You are participating in a formal debate. Be precise and evidence-aware.",
                    user_prompt=prompt,
                )

            speech_path = config.speeches_dir / f"Round_{round_num}" / f"Speaker_{idx}_{debater.alias}.md"
            speech_path.write_text(speech + "\n", encoding="utf-8")

            with transcript_path.open("a", encoding="utf-8") as f:
                f.write(f"## Round {round_num} - Speaker {idx} ({debater.alias})\n\n{speech}\n\n")

            logs.append(
                {
                    "round": round_num,
                    "speaker_index": idx,
                    "alias": debater.alias,
                    "model": debater.model,
                    "speech_path": str(speech_path),
                }
            )
    return logs


def main() -> None:
    objective_path = Path("OBJECTIVE.md")
    if not objective_path.exists():
        raise FileNotFoundError("OBJECTIVE.md not found.")

    config = parse_objective(objective_path)
    ensure_dirs(config)

    dry_run = os.getenv("DEBATE_DRY_RUN", "false").lower() == "true"
    client = None if dry_run else OpenRouterClient()

    if dry_run:
        class DummyClient:
            @staticmethod
            def chat(model: str, system_prompt: str, user_prompt: str) -> str:  # noqa: ARG004
                return f"[DRY RUN] model={model}"

        client = DummyClient()

    run_research(client, config, dry_run=dry_run)
    logs = run_debate(client, config, dry_run=dry_run)

    if config.save_json_log:
        log_file = config.transcript_dir / "run_log.json"
        log_file.write_text(json.dumps(logs, indent=2), encoding="utf-8")

    print("Debate generation complete.")


if __name__ == "__main__":
    main()
