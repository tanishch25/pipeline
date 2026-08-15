import math
from models.schemas import LLMAuditResult, TechnicalAuditMetrics, ScoringResult, PriorityTier

class RevampScorer:
    def __init__(self):
        # Balanced weights for Functionality, Design, and Problems
        self.base_weights = {
            "mobile_ux": 0.15,
            "booking_ordering_integration": 0.15,
            "page_speed_and_assets": 0.05,
            "design_modernity": 0.20,
            "cta_clarity": 0.15,
            "social_proof_trust": 0.15,
            "seo_and_schema": 0.15
        }
        
    def _exponential_curve(self, score: float, severity_factor: float = 1.2) -> float:
        """
        Converts a linear LLM score (1-10) where 1 is worst, to a deficiency metric (0-10) 
        where 10 is maximum deficiency, using an exponential curve to heavily penalize scores < 5.
        """
        deficiency = max(0.0, 10.0 - score)
        return (deficiency ** severity_factor)

    def calculate_score(self, llm_result: LLMAuditResult, tech_metrics: TechnicalAuditMetrics) -> ScoringResult:
        
        # 1. Base LLM Curve Calculation
        raw_deficiency = 0.0
        
        vectors = [
            ("Mobile UX", llm_result.mobile_ux, "mobile_ux"),
            ("Call to Action", llm_result.cta_clarity, "cta_clarity"),
            ("Booking/Ordering", llm_result.booking_ordering_integration, "booking_ordering_integration"),
            ("Design Modernity", llm_result.design_modernity, "design_modernity"),
            ("Speed & Assets", llm_result.page_speed_and_assets, "page_speed_and_assets"),
            ("SEO", llm_result.seo_and_schema, "seo_and_schema"),
            ("Trust/Social Proof", llm_result.social_proof_trust, "social_proof_trust")
        ]
        
        for name, vector, key in vectors:
            curved_def = self._exponential_curve(vector.score)
            raw_deficiency += curved_def * self.base_weights[key]
            
        base_revamp_score = raw_deficiency * 10
        
        # 2. Friction Index
        # Compounding penalty if site is slow AND hard to use on mobile AND hard to book.
        mobile_def = self._exponential_curve(llm_result.mobile_ux.score)
        booking_def = self._exponential_curve(llm_result.booking_ordering_integration.score)
        
        friction_index = 0.0
        if tech_metrics.load_time_seconds > 3.5:
            friction_multiplier = tech_metrics.load_time_seconds / 3.0
            friction_index = (mobile_def + booking_def) * friction_multiplier * 1.5

        # 3. Trust Deficit Multiplier
        trust_multiplier = 1.0
        trust_def = self._exponential_curve(llm_result.social_proof_trust.score)
        if not tech_metrics.has_ssl:
            if trust_def > 6.0:
                trust_multiplier = 1.35
            else:
                trust_multiplier = 1.15
                
        if not tech_metrics.is_mobile_responsive:
            trust_multiplier += 0.20
            
        # 4. Final Aggregation with Asymptotic Bounding
        unbounded_score = (base_revamp_score + friction_index) * trust_multiplier
        
        k = 0.015
        final_score = 100.0 * (1.0 - math.exp(-k * unbounded_score))
        final_score = min(99.9, final_score)
        
        # 5. Determine tier dynamically
        if final_score >= 75:
            tier = PriorityTier.HIGH
        elif final_score >= 45:
            tier = PriorityTier.MEDIUM
        else:
            tier = PriorityTier.LOW
            
        # 6. Compile reasoning and defects
        defects = []
        reasoning_parts = []
        
        # Sort by score ascending (worst scores first)
        vectors.sort(key=lambda x: x[1].score)
        
        for name, vector, key in vectors:
            if vector.score <= 5.0:
                if len(defects) < 3: 
                    defects.append(f"{name} Issue: {vector.reasoning}")
                reasoning_parts.append(f"- {name} ({vector.score}/10): {vector.reasoning}")
                
        if not tech_metrics.has_ssl: defects.append("Missing SSL Security")
        if not tech_metrics.is_mobile_responsive: defects.append("Fails Mobile Responsive Check")
        if tech_metrics.load_time_seconds > 4.0: defects.append(f"Slow Load Time ({tech_metrics.load_time_seconds}s)")
        
        ai_reasoning = "\n".join(reasoning_parts) if reasoning_parts else "Site passes basic heuristic checks."
        if friction_index > 10:
            ai_reasoning += f"\n- High Friction Index ({round(friction_index, 1)}) detected due to compounding speed/UX issues."
        if trust_multiplier > 1.0:
            ai_reasoning += f"\n- Trust Deficit Multiplier ({round(trust_multiplier, 2)}x) applied."
            
        return ScoringResult(
            raw_technical_score=round(friction_index, 2),
            llm_deficiency_score=round(base_revamp_score, 2),
            final_revamp_score=round(final_score, 2),
            priority_tier=tier,
            ai_reasoning=ai_reasoning,
            defects=defects
        )
