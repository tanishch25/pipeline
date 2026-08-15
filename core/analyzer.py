import json
from litellm import acompletion
from models.schemas import LLMAuditResult, TechnicalAuditMetrics
from config.settings import settings

class LLMAnalyzer:
    def __init__(self, engine: str = "hybrid"):
        if engine == "local":
            self.model = "ollama/llama3.1"
            self.fallback_model = "ollama/llama3.1"
        elif engine == "cloud":
            self.model = "groq/llama-3.1-8b-instant"
            self.fallback_model = "groq/llama-3.1-8b-instant"
        else: # hybrid
            self.model = "groq/llama-3.1-8b-instant"
            self.fallback_model = "ollama/llama3.1"
        
    async def analyze(self, text_content: str, tech_metrics: TechnicalAuditMetrics, niche: str) -> LLMAuditResult:
        # Truncate content to avoid token limits (Groq allows 8k context)
        text_content = text_content[:15000] 
        
        prompt = f"""
You are an expert web designer and conversion rate optimizer. 
Audit the following {niche} website content and technical metrics to evaluate its revamp needs.

Technical Metrics:
- SSL: {tech_metrics.has_ssl}
- Load Time: {tech_metrics.load_time_seconds}s
- Mobile Responsive: {tech_metrics.is_mobile_responsive}
- Tech Stack: {', '.join(tech_metrics.detected_tech_stack)}

Website Text Content:
{text_content}

Evaluate the site on the following 7 vectors on a scale of 0.0 (perfect) to 10.0 (terrible/desperately needs fix).
Format the output as a JSON object with scores out of 10 and very brief 1-sentence reasoning for each.
BE EXTREMELY CONCISE to save time. Maximum 1 sentence per reasoning field. Return your evaluation as a strict JSON object matching this schema exactly (no markdown, just raw JSON):
{{
    "design_modernity": {{"score": float, "reasoning": "[What is wrong] - [Why it hurts conversions] - [How to improve it]"}},
    "mobile_ux": {{"score": float, "reasoning": "..."}},
    "cta_clarity": {{"score": float, "reasoning": "..."}},
    "booking_ordering_integration": {{"score": float, "reasoning": "..."}},
    "page_speed_and_assets": {{"score": float, "reasoning": "..."}},
    "seo_and_schema": {{"score": float, "reasoning": "..."}},
    "social_proof_trust": {{"score": float, "reasoning": "..."}}
}}

Make sure the reasoning ALWAYS follows the 3-part format: [What is wrong] - [Why it hurts conversions] - [How to improve it]. Be extremely specific to the text provided.
"""
        
        try:
            if self.model == "groq/llama-3.1-8b-instant":
                try:
                    response = await acompletion(
                        model="openai/llama-3.1-8b-instant",
                        api_base="https://api.groq.com/openai/v1",
                        api_key=settings.GROQ_API_KEY,
                        messages=[{"role": "user", "content": prompt}],
                        max_retries=settings.LITELLM_MAX_RETRIES
                    )
                except Exception as e:
                    print(f"Groq API failed in Analyzer ({e}). Falling back to local Ollama...")
                    response = await acompletion(
                        model="ollama/llama3.1",
                        messages=[{"role": "user", "content": prompt}],
                        max_retries=settings.LITELLM_MAX_RETRIES
                    )
            else:
                response = await acompletion(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_retries=settings.LITELLM_MAX_RETRIES
                )
        except Exception as e:
            raise Exception(f"LLM Analysis failed entirely: {e}")
        
        content = response.choices[0].message.content

        
        # Robustly extract JSON block
        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1:
            content = content[start:end+1]
            
        data = json.loads(content)
        return LLMAuditResult(**data)
