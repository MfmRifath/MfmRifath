<!--
  Rifath MFM — GitHub profile README

  Every SVG is generated; none is hand-edited. Each exists in a light and a
  `-dark` variant, picked per GitHub theme by the <picture> elements below.

    scripts/design.py        shared tokens, type, grid, motion, primitives
    scripts/build_assets.py  static assets -> assets/*.svg      (run by hand)
    scripts/gen_stats.py     data cards    -> assets/generated/ (CI, daily)

  Tagline (marquee) lines and the featured-repo list live at the top of
  gen_stats.py; rebuild static assets with `python scripts/build_assets.py`.
-->

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/hero-dark.svg" />
  <img src="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/hero.svg" width="100%" alt="Rifath MFM — AI engineer. LLM fine-tuning, RAG and agents, real-time ML. Open to AI/ML engineering roles from November 2026." />
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/marquee-dark.svg" />
  <img src="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/marquee.svg" width="100%" alt="Real-time fraud scoring — p95 6.6 ms, champion/challenger MLOps · Fine-tuning Llama 3 with QLoRA for Tamil-medium physics · Hybrid RAG — retrieval beats a bigger model · Kafka + Avro streams with retry and dead letter queues" />
</picture>

<p align="center">
  <a href="https://my-portfolio-two-gilt-26.vercel.app/"><b>Portfolio ↗</b></a>&nbsp;&nbsp;·&nbsp;&nbsp;
  <a href="https://linkedin.com/in/rifath-mohammed-b3987a31a"><b>LinkedIn ↗</b></a>&nbsp;&nbsp;·&nbsp;&nbsp;
  <a href="mailto:mmfmrifath@gmail.com"><b>Email ↗</b></a>&nbsp;&nbsp;·&nbsp;&nbsp;
  <a href="https://twitter.com/mfmrifathmfmr"><b>X ↗</b></a>
</p>

<br/>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/section-01-about-dark.svg" />
  <img src="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/section-01-about.svg" width="100%" alt="01 — About" />
</picture>

<table>
<tr>
<td width="33%" valign="top">

<img src="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/portrait.jpg" width="100%" alt="Rifath MFM" />

</td>
<td width="67%" valign="top">

AI engineer working on **retrieval-augmented and agentic systems for education**, with a
focus on languages that large models handle badly. My final-year project fine-tunes Llama 3
on Tamil-medium A/L Physics and wraps it in a LangGraph agent with knowledge tracing — the
kind of system where the retrieval layer matters more than the model.

Lately I've been building the **production side of ML**: a real-time fraud-scoring
service with streaming features, a champion/challenger MLOps loop and drift-triggered
retraining, plus Kafka pipelines that retry, back off and dead-letter properly.

Before that: four shipped products, and six months building a national legislation
database as a backend engineer. I like problems where the data pipeline is the hard part.

```yaml
role:     AI Engineer
focus:    QLoRA · RAG · agents · real-time ML
stack:    Python · LangGraph · FastAPI · Kafka · MLflow
edu:      BSc (Hons) Software Engineering, Univ. of Ruhuna (final yr)
based:    Colombo, LK — UTC+5:30
langs:    Tamil · English · Sinhala
open_to:  AI/ML roles from Nov 2026
```

</td>
</tr>
</table>

<table>
<tr>
<td width="50%" valign="top">

**Experience**

**SE Intern** · Paralegal · *6 mo*
Sri Lankan legislation database from scratch — scraping pipeline, multilingual FastAPI
backend, React search frontend, Docker deployment.

**BSc (Hons) Software Engineering** · Univ. of Ruhuna · *final year*
FYP: AI Tuition Master.

**Content creator** · Nova Learn · *ongoing*
Tamil A/L material — Physics, Chemistry, Biology, Combined Maths.

</td>
<td width="50%" valign="top">

**Now**

| Since | What |
|:--|:--|
| Oct 2026 | FraudShield — real-time fraud scoring with an MLOps loop |
| Sep 2026 | Kafka + Avro streaming: retry, backoff, dead letter queues |
| Aug 2026 | Shopify theme engineering · a full-stack finance tracker |
| Jul 2026 | TalentScout AI · a 30-week AI engineering roadmap |
| Jun 2026 | Bayesian Knowledge Tracing for adaptive sequencing |

```ini
LEARNING     = MLOps · stream processing · LLM evals
ASK_ME_ABOUT = RAG · LLMs · Kafka · Flutter · security
```

</td>
</tr>
</table>

<br/>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/section-02-tuition-dark.svg" />
  <img src="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/section-02-tuition.svg" width="100%" alt="02 — AI Tuition Master" />
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/tuition-master-dark.svg" />
  <img src="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/tuition-master.svg" width="100%" alt="AI Tuition Master architecture: student to LangGraph router; retriever, solver agent and multimodal tools; QLoRA-tuned Llama 3; groundedness check; answer; Bayesian knowledge tracing feeds the next question back to the student." />
</picture>

An intelligent tutoring system for Tamil-medium A/L Physics. **Why it is not just a chatbot:**
answers are refused or re-retrieved when the groundedness check fails, and the next question
is chosen from a live mastery estimate rather than a fixed syllabus order.
`Python` `Llama 3` `QLoRA / PEFT` `LangGraph` `OpenAI SDK` `FastAPI`

<br/>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/section-03-fraudshield-dark.svg" />
  <img src="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/section-03-fraudshield.svg" width="100%" alt="03 — FraudShield" />
</picture>

<a href="https://github.com/MfmRifath/FraudShield">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/fraudshield-dark.svg" />
  <img src="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/fraudshield.svg" width="100%" alt="FraudShield architecture: FastAPI scoring (rules, LightGBM, calibration, cost policy) into approve, review or block; Redpanda and Redis streaming features; drift-triggered retraining with an MLflow champion/challenger hot reload. Measured: 6.6 ms p95 scoring, 100.6 req/s with 0 failures, 0 failures with Redis killed, 199 MiB demo container." />
</picture>
</a>

Real-time card-fraud detection, **built the way a production system would be.** Features are
point-in-time correct and computed identically online and offline; Redis can die mid-load
and scoring degrades instead of failing; drift triggers retraining, and a challenger has to
beat the champion at a promotion gate before it is hot-reloaded. Every number above is
written by a `make` target into the repo's `reports/` — none are typed in by hand.
`Python` `FastAPI` `LightGBM` `Redpanda / Kafka` `Redis` `MLflow` `Prometheus` `Docker`

<br/>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/section-04-work-dark.svg" />
  <img src="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/section-04-work.svg" width="100%" alt="04 — Selected work" />
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/generated/repos-dark.svg" />
  <img src="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/generated/repos.svg" width="100%" alt="Featured repositories with description, language, stars, forks and last push" />
</picture>

| No. | Project | What it does | Stack | Status |
|:-:|:--|:--|:--|:--|
| 01 | [**AI Tuition Master**](https://github.com/MfmRifath?tab=repositories) | Tamil-medium physics tutor — fine-tuned Llama 3, hybrid RAG, LangGraph agent, knowledge tracing | `Python` `LangGraph` | Building |
| 02 | [**FraudShield**](https://github.com/MfmRifath/FraudShield) | Real-time fraud scoring with reason codes, streaming features, champion/challenger MLOps, drift monitoring | `FastAPI` `LightGBM` `Kafka` | Building |
| 03 | [**TalentScout AI**](https://github.com/MfmRifath/TalentScout-AI) | Evidence-based recruitment platform — every ranking points at a commit, rubric answer or work sample; only a person may reject | `Python` `TypeScript` | Building |
| 04 | [**Kafka Order Pipeline**](https://github.com/MfmRifath/kafka-order-pipeline) | Avro-encoded order stream with real-time aggregation, backoff retry, a dead letter queue and a live demo dashboard | `Kafka` `Avro` `Python` | Shipped |
| 05 | [**AI Engineering Roadmap**](https://github.com/MfmRifath/ai-engineering-roadmap) | A 30-week, book-driven path from `sklearn.fit()` to shipping LLM systems — five books, six projects | `Python` | Building |
| 06 | [**NovaAI Bot**](https://github.com/MfmRifath/NovaAiTelegram-Bot) | Telegram tutor for A/L science — GPT-5 with Claude and Gemini fallback, photo problem solving, LaTeX output | `Python` `LLMs` | Shipped |
| 07 | [**Expense Tracker**](https://github.com/MfmRifath/Expnaces-Track) | Day / month / year finance dashboard, loan ledgers, budgets, recurring entries, CSV import | `FastAPI` `React` | Shipped |
| 08 | [**Purelane × Shopify**](https://github.com/MfmRifath/purelane-shopify) | A homepage prototype rebuilt as five production Shopify sections on Dawn 15.5 | `Liquid` `JS` | Shipped |

<details>
<summary><b>Earlier work</b> — shipped mobile and web products</summary>
<br/>

| Project | What it does | Stack |
|:--|:--|:--|
| [**S2O Academy**](https://github.com/MfmRifath/S2O-Website) | Academy platform front end | `TypeScript` |
| [**LearnWithUsama**](https://github.com/MfmRifath/LearnWithUsama) | EdTech mobile app — gamified practice, real-time quizzes, progress tracking | `Flutter` `Firebase` |
| [**Nova Science**](https://github.com/MfmRifath/NOVA-SCIENCE) | Online learning platform | `Flutter` `Dart` |
| [**Zing**](https://github.com/MfmRifath/Zing_website) | Commerce app — secure payments, real-time cart, inventory | `TypeScript` |
| [**Calorie Tracker**](https://github.com/MfmRifath/Calorie-Tracker-App---Flutter---Dart) | Intake vs. burn, local SQL persistence, analytics charts | `Flutter` `SQL` |

</details>

<br/>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/section-05-stack-dark.svg" />
  <img src="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/section-05-stack.svg" width="100%" alt="05 — Stack" />
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/stack-dark.svg" />
  <img src="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/stack.svg" width="100%" alt="Stack. AI/ML: Python, PyTorch, Hugging Face, QLoRA/PEFT, Llama 3, hybrid RAG, LightGBM, TensorFlow. Agents: LangGraph, LangChain, OpenAI SDK, Claude API, AutoGen. Streaming/MLOps: Kafka/Avro, Redis, MLflow, Prefect, Prometheus, Grafana. Backend: FastAPI, Django, Spring Boot, Node.js, Java. Data: PostgreSQL, MySQL, SQLite, MongoDB, Firebase. Mobile/Web: Flutter, React, TypeScript, Dart, Android, Tailwind, Shopify/Liquid. Infra: Docker, GitHub Actions, Vercel, Git, Linux, Postman. Security: Kali Linux, TryHackMe, Wireshark, Burp Suite." />
</picture>

<br/>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/section-06-activity-dark.svg" />
  <img src="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/section-06-activity.svg" width="100%" alt="06 — Activity" />
</picture>

<!-- Rendered daily by scripts/gen_stats.py from the GitHub GraphQL API. -->

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/generated/stats-dark.svg" />
  <img src="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/generated/stats.svg" width="49%" alt="Commits, stars, repos, active days, best streak and followers" />
</picture>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/generated/languages-dark.svg" />
  <img src="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/generated/languages.svg" width="49%" alt="Most-used languages by bytes across owned repositories" />
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/generated/activity-dark.svg" />
  <img src="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/generated/activity.svg" width="100%" alt="Contribution heatmap for the last year" />
</picture>

<br/>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/section-07-contact-dark.svg" />
  <img src="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/section-07-contact.svg" width="100%" alt="07 — Contact" />
</picture>

<a href="mailto:mmfmrifath@gmail.com">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/contact-dark.svg" />
  <img src="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/contact.svg" width="100%" alt="Let's talk. mmfmrifath@gmail.com. Open to AI/ML engineering roles from November 2026." />
</picture>
</a>

<img src="https://raw.githubusercontent.com/MfmRifath/MfmRifath/main/assets/portrait-wide.jpg" width="100%" alt="Rifath MFM" />

<p align="center">
  <a href="mailto:mmfmrifath@gmail.com"><b>mmfmrifath@gmail.com</b></a>&nbsp;&nbsp;·&nbsp;&nbsp;
  <a href="https://my-portfolio-two-gilt-26.vercel.app/">Portfolio ↗</a>&nbsp;&nbsp;·&nbsp;&nbsp;
  <a href="https://linkedin.com/in/rifath-mohammed-b3987a31a">LinkedIn ↗</a>&nbsp;&nbsp;·&nbsp;&nbsp;
  <a href="https://github.com/MfmRifath">GitHub ↗</a>
</p>
