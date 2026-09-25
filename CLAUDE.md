# Parent Wise — project constitution

Every Claude step reads this first.

## What this is
Automated social-media content factory for the **parenting / child development** niche (@parentwise__).
Twice a day it collects news and builds verified post candidates; when the owner picks one it produces a carousel, a voiced
video, a cover and a caption, and after approval publishes to Instagram, Facebook and YouTube.

## Audience & language
- Audience: parents of babies, toddlers, kids and teens (international, English-speaking).
- Content language: **English**. Owner communication (Studio UI, Telegram, candidate `summary_tr` / `why_tr`): **Turkish**.
- Tone: warm, calm, practical, non-judgmental. Never shame parents. No fear-mongering, no "shocking" clickbait.

## Two pillars
1. **Verified news posts** (research, guidelines, recalls, policy changes, product safety).
2. **Copy-paste playbooks** — reusable cards: scripts to say to a child, checklists, routines, conversation starters
   (the parenting equivalent of "prompt packs"). Plus evergreen tips.

## Hard rules (non-negotiable)
- Every factual sentence is verified against an official source (AAP, WHO, CDC, NHS, NIH/NICHD, UNICEF, CPSC, FDA,
  peer-reviewed journal, manufacturer recall notice). Source URLs go into the content JSON `sources`. Unverifiable claims are dropped.
- HN / Reddit / blogs = hints only, never a source.
- **Medical/safety**: every post carries "General information, not medical advice. Talk to your pediatrician." in the caption
  and on the last slide. Never give dosages, diagnoses or "cure" claims. Never contradict AAP/WHO guidance.
- Product recalls: product, hazard and remedy exactly as the CPSC/FDA notice says; link the notice.
- **Children's privacy**: never use photos of real, identifiable children. Covers = licensed photos of adult experts
  (Wikimedia CC BY / CC BY-SA / CC0 / public domain only) or generated scenes with no children's faces, no text, no logos.
- No invented quotes, statistics, endorsements or "doctor approved" badges. No fake verified badge. No logo imitation.
- No repeats: a topic already posted never becomes a candidate again (code filter + scout rule).
- Human approval for every post during the first 2 weeks; a QA failure always forces approval.
- Zero cost: only free official APIs, OFL fonts, code-drawn visuals, procedural music, local TTS / image models.
- Viral clips: IG + FB Reels only, with credit; never YouTube. Skip clips that mock or expose private moments of minors.

## Content rules
- Carousel: 7–10 slides. Cover hook 8–22 words, accurate, no invented numbers.
- Caption: hook line first, 2–4 short lines, save/follow CTA, 4–8 hashtags, disclaimer line.
- Voiceover: 7–15 words per slide, conversational, verified facts only. Video 30–40 s.
- Age ranges always explicit ("6–12 months"). Culture-neutral wording.

## Layout
studio.py (engine + UI server), news.py, publish.py, cover.py, carousel.py, reel.py, clip.py, voice.py, music.py,
metrics.py, telegram_bot.py, themes/, prompts/, content/, research/, output/ (ignored), runs/ (ignored), fonts/.
