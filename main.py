import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint
import csv
from typing import Optional

from storage.database import init_db, AsyncSessionLocal
from core.scraper import LeadScraper
from core.auditor import WebsiteAuditor
from core.analyzer import LLMAnalyzer
from core.scorer import RevampScorer
from core.pitcher import PitchGenerator
from core.tracker import AnalyticsTracker
from storage.models import Lead, PitchRecord, AuditResult
from sqlalchemy import select

app = typer.Typer(help="Lead Gen Pipeline CLI")
console = Console()

global_state = {"should_stop": False}

async def run_pipeline_async(query: str = "Test Gyms", limit: int = 5, mock_mode: bool = False, engine: str = "hybrid", auto_send: bool = False):
    """
    Core pipeline logic running asynchronously.
    Yields string updates for UI consumption.
    """
    yield f"Starting pipeline for '{query}' with limit {limit}. Engine: {engine}. Auto-send: {auto_send}"
    await init_db()
    
    scraper = LeadScraper(headless=True)
    auditor = WebsiteAuditor()
    analyzer = LLMAnalyzer(engine=engine)
    scorer = RevampScorer()
    pitcher = PitchGenerator(engine=engine)
    
    async with AsyncSessionLocal() as session:
        tracker = AnalyticsTracker(session)
        
        # 1. Scrape Leads
        queries = [q.strip() for q in query.split(",") if q.strip()]
        yield f"Scraping for {len(queries)} queries: {', '.join(queries)}"
        
        all_leads = []
        if mock_mode:
            # Mock data
            from models.schemas import LeadRecord, NicheType
            all_leads = [
                LeadRecord(name="Test Gym", niche=NicheType.GYM, website_url="https://example.com")
            ]
        else:
            for q in queries:
                if global_state["should_stop"]:
                    yield "Pipeline stopped by user. Halting scraping."
                    break
                    
                yield f"Running scraper for: {q}"
                leads = await scraper.scrape(query=q, limit=limit)
                all_leads.extend(leads)
                
        yield f"Found {len(all_leads)} total leads before deduplication."
        
        # Deduplication against Database
        processed_count = 0
        for lead_data in all_leads:
            if global_state["should_stop"]:
                yield "Pipeline stopped by user. Halting lead processing."
                break
                
            try:
                # Check if website_url exists in DB
                existing_lead_stmt = select(Lead).where(Lead.website_url == lead_data.website_url)
                existing_lead_result = await session.execute(existing_lead_stmt)
                if existing_lead_result.scalars().first():
                    yield f"Skipping {lead_data.name} (URL already exists in DB: {lead_data.website_url})"
                    continue
                    
                processed_count += 1
                yield f"\nProcessing ({processed_count}): {lead_data.name} ({lead_data.website_url})"
                
                # DB Insert
                db_lead = await tracker.add_lead(lead_data)
                
                if mock_mode:
                    from models.schemas import TechnicalAuditMetrics
                    tech_metrics = TechnicalAuditMetrics(
                        has_ssl=False, load_time_seconds=5.0, is_mobile_responsive=False,
                        detected_tech_stack=["WordPress"], meta_description_present=False,
                        h1_count=1, has_broken_ctas=True
                    )
                    text_content = "Welcome to Test Gym. We have weights."
                    found_email = "test@example.com"
                    social_links = {"facebook_url": None, "twitter_url": None, "instagram_url": None, "linkedin_url": None}
                else:
                    tech_metrics, text_content, found_email, social_links = await auditor.audit(lead_data.website_url)
                    
                # Update email and social links if found
                if not mock_mode and (found_email or any(social_links.values())):
                    if found_email: lead_data.email = found_email
                    lead_data.facebook_url = social_links.get("facebook_url")
                    lead_data.twitter_url = social_links.get("twitter_url")
                    lead_data.instagram_url = social_links.get("instagram_url")
                    lead_data.linkedin_url = social_links.get("linkedin_url")
                    
                    # We need to update the DB record since we already inserted it
                    async with AsyncSessionLocal() as update_session:
                        update_lead = await update_session.get(Lead, db_lead.id)
                        if update_lead:
                            if found_email: update_lead.email = found_email
                            update_lead.facebook_url = lead_data.facebook_url
                            update_lead.twitter_url = lead_data.twitter_url
                            update_lead.instagram_url = lead_data.instagram_url
                            update_lead.linkedin_url = lead_data.linkedin_url
                            await update_session.commit()
                    
                await tracker.update_status(db_lead.id, "AUDITED")
                
                # LLM Analyze
                yield "Running LLM Analysis..."
                if mock_mode:
                    from models.schemas import LLMAuditResult, VectorScore
                    mock_vector = VectorScore(score=7.5, reasoning="Mock reasoning")
                    llm_audit = LLMAuditResult(**{k: mock_vector for k in LLMAuditResult.model_fields})
                else:
                    llm_audit = await analyzer.analyze(text_content, tech_metrics, lead_data.niche)
                    
                scoring_result = scorer.calculate_score(llm_audit, tech_metrics)
                yield f"Score: {scoring_result.final_revamp_score}/100 (Tier: {scoring_result.priority_tier.value})"
                
                await tracker.save_audit(
                    lead_id=db_lead.id,
                    score_data=scoring_result,
                    has_ssl=tech_metrics.has_ssl,
                    load_time=tech_metrics.load_time_seconds,
                    is_mobile=tech_metrics.is_mobile_responsive
                )
                await tracker.update_status(db_lead.id, "SCORED")
                
                # Pitch Generate ONLY if score >= 70.0
                if scoring_result.final_revamp_score >= 70.0:
                    yield "Lead score >= 70. Generating personalized pitch..."
                    if mock_mode:
                        from models.schemas import PitchPayload
                        pitch = PitchPayload(
                            subject_line="Mock Pitch Subject",
                            body_text="This is a mock pitch for a dry run.",
                            compliment="Nice mock gym",
                            identified_flaws=["Mock flaw"]
                        )
                    else:
                        pitch = await pitcher.generate(lead_data, scoring_result.defects)
                        
                    await tracker.save_pitch(db_lead.id, pitch)
                    await tracker.update_status(db_lead.id, "PITCH READY")
                    
                    yield "\nPitch Draft Generated (Saved to DB):"
                    yield f"Subject: {pitch.subject_line}"
                    yield f"Body:\n{pitch.body_text}\n"
                    
                    if auto_send:
                        if lead_data.email:
                            yield f"Auto-sending email to {lead_data.email}..."
                            from core.mailer import Mailer
                            mailer = Mailer()
                            success = mailer.send_email(
                                to_email=lead_data.email,
                                subject=pitch.subject_line,
                                body=pitch.body_text
                            )
                            if success:
                                await tracker.update_status(db_lead.id, "SENT")
                                yield "Auto-send successful."
                            else:
                                yield "Auto-send failed (check SMTP settings)."
                        else:
                            yield "Auto-send skipped (no email address found)."
                            
                else:
                    yield "Lead score is below 70. Skipping pitch generation."
                
            except Exception as e:
                import traceback
                yield f"Error processing {lead_data.name}: {e}\n{traceback.format_exc()}"

@app.command()
def run_pipeline(query: str = "Test Gyms", limit: int = 5, mock: int = 0):
    """Run the end-to-end lead generation pipeline."""
    dry_run = mock == 1
    async def _run():
        async for msg in run_pipeline_async(query, limit, mock_mode=dry_run):
            console.print(msg)
    asyncio.run(_run())

@app.command()
def show_analytics():
    """Print a rich formatted table of funnel stats."""
    async def _show():
        await init_db()
        async with AsyncSessionLocal() as session:
            tracker = AnalyticsTracker(session)
            stats = await tracker.get_funnel_stats()
            
            table = Table(title="Pipeline Analytics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")
            
            for k, v in stats.items():
                table.add_row(k, str(v))
                
            console.print(table)
            
    asyncio.run(_show())

@app.command()
def export_pitches(min_score: float = 70.0, output: str = "leads.csv"):
    """Export pitched leads to a CSV file."""
    async def _export():
        await init_db()
        async with AsyncSessionLocal() as session:
            # Join Lead, AuditResult, PitchRecord
            stmt = select(Lead, AuditResult, PitchRecord).join(AuditResult).join(PitchRecord).where(AuditResult.final_revamp_score >= min_score)
            result = await session.execute(stmt)
            rows = result.all()
            
            with open(output, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Business Name", "Website", "Score", "Subject", "Body"])
                for lead, audit, pitch in rows:
                    writer.writerow([lead.name, lead.website_url, audit.final_revamp_score, pitch.subject_line, pitch.body_text])
            
            console.print(f"[green]Exported {len(rows)} pitches to {output}[/green]")
            
    asyncio.run(_export())

if __name__ == "__main__":
    app()
