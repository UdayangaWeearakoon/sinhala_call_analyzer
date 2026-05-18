# Customer Intelligence Platform — Roadmap

> Vision: Evolve Sinhala Call Analytics from a sentiment classifier into a full "Voice of Customer Operating System" that surfaces *why* customers are unhappy, *which* areas are failing, and *what* actions to take.

## Current State

- **ML**: XLM-RoBERTa → XGBoost for category (e.g. "Billing") + sentiment (Positive/Neutral/Negative)
- **Backend**: FastAPI + MongoDB Atlas (Beanie ODM) — 6 endpoints
- **Frontend**: React + Vite + TailwindCSS + Recharts — single Overview page with KPIs, donut, trend, top categories, recent calls, ingest form
- **Key detail**: 768-dim embeddings already computed in `preprocessor.py` but NOT stored in DB

---

## Stage 1 — Topic Clustering (1-2 days)
*"Surface unknown complaint clusters without anyone defining rules."*

- [ ] Add `embedding` field (list[float]) to `Call` Beanie model
- [ ] Store 768-dim vector on ingest: `predictor.preprocessor.get_embeddings(transcript).tolist()`
- [ ] Run KMeans (silhouette score for auto-k) on stored embeddings — on-demand or periodic
- [ ] Expose `GET /api/analytics/emerging-topics` — cluster label, representative transcripts, volume trend
- [ ] Frontend: "Emerging Topics" card on Overview page

## Stage 2 — Emotion + Intent (3-5 days)
*"Connect how people feel with why they called."*

- [ ] Generate labeled data via Gemini for emotions (frustrated, confused, satisfied, angry, urgent) and intents (refund_request, tech_support, cancellation, billing_inquiry, feature_request)
- [ ] Train two new XGBoost models (emotion + intent) — shares same embeddings
- [ ] Add `emotion` and `intent` fields to `Call` model
- [ ] Run all 4 models on every ingest (virtually free since embedding is cached)
- [ ] Expose in API + update dashboard

## Stage 3 — Root Cause + Keyword Mining (3-4 days)
*"Make every call searchable by what actually happened."*

- [ ] Add `keywords` (list[str]) extracted via TF-IDF against full corpus — top 3-5 terms per call
- [ ] Add `root_cause` field — rule-based or small NER: "app crashed after payment" → {area, issue, severity}
- [ ] Expose `GET /api/analytics/search/keywords?q=overcharged` — full-text search across transcripts + keywords
- [ ] Frontend: new "Voice Explorer" page with keyword cloud + searchable transcript snippets

## Stage 4 — Predictive Layer: Urgency + Churn (4-5 days)
*"System proactively warns management before problems escalate."*

- [ ] **Urgency score** (0-1): heuristic + ML — features: negative emotion, competitor mentions, cancellation phrases, repeat calls
- [ ] **Churn risk**: phone-level aggregation — track call frequency, sentiment trajectory, escalation phrases → risk levels (low/medium/high)
- [ ] **Early warning**: z-score anomaly on DailyAggregate — flag when daily negative % deviates > 2σ from 7-day rolling
- [ ] Expose `GET /api/analytics/alerts`
- [ ] Frontend: new "Predictive" page with churn risk panel + alert feed

## Stage 5 — Decision Layer: Insights + Recommendations (5-7 days)
*"Management gets a story, not just numbers."*

- [ ] **AI Insight Generator**: weekly endpoint → Gemini summarizes past 7 days → 3-5 natural language bullets
- [ ] **Priority Action Board**: rank issues by (volume × negativity × trend_direction) with estimated impact
- [ ] **"What-If" Simulator**: given hypothetical reduction in category negative rate, recompute overall sentiment
- [ ] Frontend: new "Decision Hub" page with digest + action board + simulator

## Immediate Parallel Tracks

- [ ] Add `react-router-dom` for frontend page routing
- [ ] Index `embedding` field in MongoDB (for future vector search)

## Architecture Principles

- No new infrastructure — MongoDB handles this scale
- Keep XGBoost-on-embeddings — proven, fast, good enough
- No agent analytics (removed intentionally)
- No geo features (no location data)
- Each stage delivers standalone value

## Ideas Captured (Not Yet Scoped)

- Emotion fingerprinting (frustrated, confused, delighted, impatient)
- Neutral sentiment deep-dive (who's about to tip)
- "Silent Problem" detector (low volume + high negativity)
- Story Mode Report (auto-generated monthly PDF/PPT)
- Feedback Loop Tracker (before/after sentiment for resolved issues)
- Sentiment Recovery Score per call (start vs end sentiment delta)
- Competitor mention tracking (strategic intelligence)
- Customer persona discovery (price-sensitive, frustrated loyalists, etc.)
- Cost of poor service dashboard (churn loss, refund cost, escalation cost)
- Sankey diagram: Call Reason → Root Cause → Outcome
- Conversation timeline analysis (sentiment changes within a single call)
- Resolution effectiveness tracking (reopened complaints, repeat callers)
