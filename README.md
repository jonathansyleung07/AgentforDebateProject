# Agent for Debate Project

This project runs a configurable **multi-agent AI debate** by reading one file: `OBJECTIVE.md`.

The script will:
- Parse debate settings (topic, rounds, debaters, models, language, word target) from `OBJECTIVE.md`
- Run pre-debate research rounds for each debater
- Generate round-by-round speeches in sequence
- Save all artifacts in organized folders (`memory/`, `speeches/`, `transcripts/`)
- Use OpenRouter API credentials from `.env`

## 1) Environment Setup (Conda + Python 3.12)

```bash
conda create -n debate-agent python=3.12 -y
conda activate debate-agent
pip install -r requirements.txt
```

## 2) API Configuration

Copy and edit environment variables:

```bash
cp .env.example .env
```

Set at least:
- `OPENROUTER_API_KEY`
- `OPENROUTER_API_URL` (default already points to OpenRouter chat completions)

Optional headers:
- `OPENROUTER_SITE_URL`
- `OPENROUTER_APP_NAME`

> `.env` is ignored by Git via `.gitignore`.

## 3) Define Your Debate Objective

Edit `OBJECTIVE.md`.

Important: include a fenced YAML block (
```yaml
...
```
) that defines:
- `topic`
- `rounds`
- `speech_word_target`
- `research_rounds_per_debater`
- `debaters` (alias/model/language/stance)
- `output` folders and options

A complete starter objective is already provided.

## 4) Run

Real API run:

```bash
python debate_agent.py
```

Dry run (no API calls, useful for testing folder/file flow):

```bash
DEBATE_DRY_RUN=true python debate_agent.py
```

## Output Structure

- `memory/<Alias>/research_round_1.md`, `research_round_2.md`, ...
- `speeches/Round_1/Speaker_1_<Alias>.md`, etc.
- `transcripts/debate_transcript.md`
- `transcripts/run_log.json` (if enabled)

## Notes

- Keep model names in `OBJECTIVE.md` compatible with OpenRouter.
- Increase or decrease `speech_word_target` based on token budget.
- You can add more debaters by extending the `debaters` list.
