import json
from typing import List
from litellm import acompletion
from models.schemas import PitchPayload, LLMAuditResult, LeadRecord
from config.settings import settings

class PitchGenerator:
    def __init__(self, engine: str = "hybrid"):
        if engine == "local" or engine == "hybrid":
            self.model = "ollama/llama3.1"
        else: # cloud
            self.model = "groq/llama-3.1-8b-instant"
        
    async def generate(self, lead_data: 'LeadRecord', identified_flaws: List[str]) -> PitchPayload:
        flaws_text = ", ".join(identified_flaws) if identified_flaws else "General outdated design and poor UX"
        
        # Load configurable prompts
        import os
        prompts_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "prompts.json")
        try:
            with open(prompts_path, 'r', encoding='utf-8') as f:
                config_prompts = json.load(f)
        except Exception:
            # Fallback if missing
            config_prompts = {}
            
        draft_template = config_prompts.get("draft_prompt", "You are an elite copywriter...\nContext:\n- Lead Name: {lead_name}\n- Their Niche: {lead_niche}\n- Their Location: {lead_city}\n- Flaws: {flaws_text}\n\nWrite a 3 sentence pitch. Format output as JSON:\n{\"subject_line\": \"...\", \"body_text\": \"...\", \"identified_flaws\": [], \"compliment\": \"...\"}")
        
        prompt = draft_template.replace("{lead_name}", lead_data.name)
        prompt = prompt.replace("{lead_niche}", lead_data.niche)
        prompt = prompt.replace("{lead_city}", lead_data.city or "Unknown")
        prompt = prompt.replace("{flaws_text}", flaws_text)
        import asyncio
        
        async def _fetch_draft(draft_id: int):
            try:
                if self.model == "groq/llama-3.1-8b-instant":
                    try:
                        resp = await acompletion(
                            model="openai/llama-3.1-8b-instant",
                            api_base="https://api.groq.com/openai/v1",
                            api_key=settings.GROQ_API_KEY,
                            messages=[{"role": "user", "content": prompt}],
                            max_retries=settings.LITELLM_MAX_RETRIES,
                            temperature=0.7 + (draft_id * 0.1) # Add slight variation
                        )
                    except Exception as e:
                        print(f"Groq API failed in Pitcher Draft {draft_id} ({e}). Falling back to local Ollama...")
                        resp = await acompletion(
                            model="ollama/llama3.1",
                            messages=[{"role": "user", "content": prompt}],
                            max_retries=settings.LITELLM_MAX_RETRIES,
                            temperature=0.7 + (draft_id * 0.1)
                        )
                else:
                    resp = await acompletion(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        max_retries=settings.LITELLM_MAX_RETRIES,
                        temperature=0.7 + (draft_id * 0.1)
                    )
                content = resp.choices[0].message.content
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end != -1:
                    content = content[start:end+1]
                return json.loads(content)
            except Exception as e:
                print(f"Draft {draft_id} failed: {e}")
                return None
                
        # 1. Generate 3 drafts concurrently
        drafts_results = await asyncio.gather(*[_fetch_draft(i) for i in range(3)])
        valid_drafts = [d for d in drafts_results if d]
        
        if not valid_drafts:
            raise Exception("Failed to generate any valid pitch drafts.")
            
        if len(valid_drafts) == 1:
            return PitchPayload(**valid_drafts[0])
            
        # 2. Evaluation Layer
        eval_template = config_prompts.get("evaluate_prompt", "Evaluate {num_drafts} drafts for {lead_name}.\n\nDrafts:\n{drafts_text}\n\nReturn JSON: {\"best_draft_index\": 0, \"reasoning\": \"...\"}")
        
        drafts_text_list = []
        for idx, draft in enumerate(valid_drafts):
            drafts_text_list.append(f"--- DRAFT {idx} ---\nSubject: {draft.get('subject_line')}\nBody: {draft.get('body_text')}\n")
        
        eval_prompt = eval_template.replace("{num_drafts}", str(len(valid_drafts)))
        eval_prompt = eval_prompt.replace("{lead_name}", lead_data.name)
        eval_prompt = eval_prompt.replace("{drafts_text}", "\n".join(drafts_text_list))
        try:
            if self.model == "groq/llama-3.1-8b-instant":
                try:
                    eval_resp = await acompletion(
                        model="openai/llama-3.1-8b-instant",
                        api_base="https://api.groq.com/openai/v1",
                        api_key=settings.GROQ_API_KEY,
                        messages=[{"role": "user", "content": eval_prompt}],
                        max_retries=settings.LITELLM_MAX_RETRIES
                    )
                except Exception as e:
                    print(f"Groq API failed in Pitcher Eval ({e}). Falling back to local Ollama...")
                    eval_resp = await acompletion(
                        model="ollama/llama3.1",
                        messages=[{"role": "user", "content": eval_prompt}],
                        max_retries=settings.LITELLM_MAX_RETRIES
                    )
            else:
                eval_resp = await acompletion(
                    model=self.model,
                    messages=[{"role": "user", "content": eval_prompt}],
                    max_retries=settings.LITELLM_MAX_RETRIES
                )
            
            eval_content = eval_resp.choices[0].message.content
            start = eval_content.find('{')
            end = eval_content.rfind('}')
            if start != -1 and end != -1:
                eval_content = eval_content[start:end+1]
                
            eval_data = json.loads(eval_content)
            best_idx = int(eval_data.get("best_draft_index", 0))
            if best_idx < 0 or best_idx >= len(valid_drafts):
                best_idx = 0
                
            best_draft = valid_drafts[best_idx]
            print(f"Evaluator selected draft {best_idx}. Reasoning: {eval_data.get('reasoning')}")
            
            # 3. Refinement Layer
            refine_template = config_prompts.get("refine_prompt", "Refine draft:\nSub: {draft_subject}\nBody: {draft_body}\n\nReturn JSON: {\"subject_line\": \"...\", \"body_text\": \"...\", \"identified_flaws\": {draft_flaws}, \"compliment\": \"{draft_compliment}\"}")
            refine_prompt = refine_template.replace("{draft_subject}", best_draft.get('subject_line', ''))
            refine_prompt = refine_prompt.replace("{draft_body}", best_draft.get('body_text', ''))
            refine_prompt = refine_prompt.replace("{draft_flaws}", json.dumps(best_draft.get('identified_flaws', [])))
            refine_prompt = refine_prompt.replace("{draft_compliment}", best_draft.get('compliment', ''))
            if self.model == "groq/llama-3.1-8b-instant":
                try:
                    refine_resp = await acompletion(
                        model="openai/llama-3.1-8b-instant",
                        api_base="https://api.groq.com/openai/v1",
                        api_key=settings.GROQ_API_KEY,
                        messages=[{"role": "user", "content": refine_prompt}],
                        max_retries=settings.LITELLM_MAX_RETRIES
                    )
                except Exception as e:
                    print(f"Groq API failed in Pitcher Refinement ({e}). Falling back to local Ollama...")
                    refine_resp = await acompletion(
                        model="ollama/llama3.1",
                        messages=[{"role": "user", "content": refine_prompt}],
                        max_retries=settings.LITELLM_MAX_RETRIES
                    )
            else:
                refine_resp = await acompletion(
                    model=self.model,
                    messages=[{"role": "user", "content": refine_prompt}],
                    max_retries=settings.LITELLM_MAX_RETRIES
                )
                
            refine_content = refine_resp.choices[0].message.content
            start = refine_content.find('{')
            end = refine_content.rfind('}')
            if start != -1 and end != -1:
                refine_content = refine_content[start:end+1]
                
            refined_data = json.loads(refine_content)
            print("Draft successfully refined in Stage 3.")
            return PitchPayload(**refined_data)
            
        except Exception as e:
            print(f"Evaluation or Refinement failed, defaulting to first draft: {e}")
            best_draft = valid_drafts[0]

        return PitchPayload(**best_draft)
