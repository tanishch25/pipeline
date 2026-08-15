# Lead Generation Pipeline

An end-to-end autonomous outbound client acquisition pipeline.

## Features
- Zero-cost architecture using Google Maps web scraping (Playwright)
- Asynchronous website auditing
- AI-driven layout & copy analysis (Gemini Flash via LiteLLM)
- Deterministic lead scoring
- Hyper-personalized cold pitch generation
- Local SQLite tracking

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. Configure environment:
   Copy `.env.example` to `.env` and set your `GEMINI_API_KEY`.

3. Run a test:
   ```bash
   python main.py run-pipeline --dry-run
   ```

4. Run for real:
   ```bash
   python main.py run-pipeline --query "Gyms in Austin TX" --limit 5
   ```

5. View Analytics:
   ```bash
   python main.py show-analytics
   ```
