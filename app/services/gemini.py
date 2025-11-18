import google.generativeai as genai
from app.config import settings
from structlog import get_logger
from pybreaker import CircuitBreaker
from app.services.promttemplet import build_reason_prompt

logger = get_logger()
breaker = CircuitBreaker(fail_max=3, reset_timeout=60)

genai.configure(api_key=settings.GEMINI_API_KEY)

@breaker
async def generate_reason(tenant_profile: dict,
                          property: dict,
                          transport_cost: float,
                          language: str,
                          context: dict | None = None) -> str:
    # Prefer Gemini 2.0 Flash, fall back to 1.5 Flash if unavailable
    primary_model = 'gemini-2.0-flash'
    fallback_model = 'gemini-1.5-flash-latest'
    lang_map = {"en": "English", "am": "Amharic", "or": "Afaan Oromo"}
    prompt = build_reason_prompt(tenant_profile, property, context, language)
    try:
        model = genai.GenerativeModel(primary_model)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # Fallback if the primary model is not available in current region/version
        logger.error("Gemini API failed on primary model", error=str(e), model=primary_model)
        try:
            model = genai.GenerativeModel(fallback_model)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e2:
            logger.error("Gemini API failed on fallback model", error=str(e2), model=fallback_model)
            return f"Reason generation failed in {lang_map[language]}."
