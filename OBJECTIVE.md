# OBJECTIVE

Build a multi-agent debate where **3 AI debaters** discuss one social problem:

> How should society solve potential mass unemployment in the post-AI era?

## Execution Configuration

```yaml
topic: "How should society solve potential mass unemployment in the post-AI era?"
rounds: 3
speech_word_target: 1000
research_rounds_per_debater: 2

debaters:
  - alias: Peter
    model: openai/gpt-4o-mini
    language: English
    stance: "Emphasize policy + social safety net"
  - alias: Paul
    model: anthropic/claude-3.5-sonnet
    language: English
    stance: "Emphasize market innovation + entrepreneurship"
  - alias: Mary
    model: google/gemini-1.5-pro
    language: Chinese
    stance: "Emphasize education reform + long-term human development"

output:
  speeches_dir: speeches
  memory_dir: memory
  transcript_dir: transcripts
  transcript_file: debate_transcript.md
  save_json_log: true
```

## Behavioral Rules

1. The program reads this file and auto-discovers all settings above.
2. Each debater performs **2 private research rounds** before public speaking.
3. Research notes must be human-readable and saved under each debater's memory folder.
4. Debate has **3 rounds**. In each round, every debater speaks once in order.
5. Before each speech, a debater may read:
   - all previous speeches from other debaters
   - their own memory folder content
6. Every speech should target around **1000 words** in the configured language.
7. Save speeches in:
   - `speeches/Round_1`, `speeches/Round_2`, `speeches/Round_3`
   - filenames like `Speaker_1_Peter.md`, `Speaker_2_Paul.md`, etc.
8. Keep an aggregated transcript in `transcripts/debate_transcript.md`.
