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
    model = genai.GenerativeModel('gemini-1.5-flash')
    lang_map = {"en": "English", "am": "Amharic", "or": "Afaan Oromo"}
    prompt = build_reason_prompt(tenant_profile, property, context, language)
    try:
        response = await model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error("Gemini API failed", error=str(e))
        return f"Reason generation failed in {lang_map[language]}."
