# sources and provenance

## Human-essay corpora (anchor)
- **Liang et al. (2023), ChatGPT-Detector-Bias.** Public human-written essays used here so that
  any detector positive is a false accusation:
  - `Human_Data/TOEFL_real_91/` — 91 TOEFL essays by non-native English writers (non-native label).
  - `Human_Data/HewlettStudentEssay_real_88/` — 88 US 8th-grade essays (native label).
  - `Human_Data/CollegeEssay_real_70/` — 70 US college admission essays (native label).
  - Repo: https://github.com/Weixin-Liang/ChatGPT-Detector-Bias
  - Paper: Liang, W., et al. (2023). GPT detectors are biased against non-native English
    writers. Patterns, 4(7), 100779. https://www.cell.com/patterns/fulltext/S2666-3899(23)00130-7
- **Optional extension corpora** (broader L1 coverage, registration-gated, used only if added):
  ICNALE (Asian L2 English); ELLIPSE (English Language Learner Insight, Proficiency and Skills
  Evaluation). Noted here for transparency; not required to reproduce the headline.

## Open-source detectors (version-pinned in run_detectors.py)
- `openai-community/roberta-base-openai-detector` — GPT-2 output detector (perplexity-family).
- `openai-community/roberta-large-openai-detector` — larger variant.
- `coai/roberta-ai-detector-v2` — 2024 RoBERTa AI-text detector.
- `fakespot-ai/roberta-base-ai-text-detection-v1` — 2024 RoBERTa AI-text detector.
  All from Hugging Face; pin the commit/revision in the run script for reproducibility.

## University academic-integrity / AI policy corpus
- Public institutional policy pages (academic-integrity offices, provost/teaching-center AI
  guidance). Each row records the source URL and access date in provenance columns. Coding
  rubric (admissibility of detector output as evidence; burden of proof; appeal pathway; any
  multilingual/L2 protection) documented in build_policy_corpus.py.

## Prior work this paper extends (not replicates)
- Liang et al. (2023), Patterns — established detector bias against non-native writers.
- Detecting ChatGPT-generated essays in a large-scale writing assessment (Computers & Education,
  2024). https://www.sciencedirect.com/science/article/abs/pii/S0360131524000848
- Different Time, Different Language: Revisiting the Bias Against Non-Native Speakers in GPT
  Detectors (2026). https://arxiv.org/abs/2602.05769
