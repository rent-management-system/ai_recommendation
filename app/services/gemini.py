import google.generativeai as genai
from app.config import settings
from structlog import get_logger
from pybreaker import CircuitBreaker

logger = get_logger()
breaker = CircuitBreaker(fail_max=3, reset_timeout=60)

genai.configure(api_key=settings.GEMINI_API_KEY)

@breaker
async def generate_reason(tenant_profile: dict, 
property: dict, transport_cost: float, language: str) -> str:
    model = genai.GenerativeModel('gemini-1.5-flash')
    lang_map = {"en": "English", "am": "Amharic", "or": "Afaan Oromo"}
    prompt = f"""
    Tenant Profile: {tenant_profile}
    Property: {property}
    Monthly Transport Cost: {transport_cost} ETB
    Generate a concise reason in {lang_map[language]} why this property is suitable.
    Consider proximity to job/school, affordability (rent ≤30% of salary), family size, amenities.
    Example (Amharic): 'ይህ አፓርትመንት በቦሌ ከሥራዎ 5 ኪ.ሜ ርቀት ላይ ነው፣ ወርሃዊ ትራንስፖርት 50 ብር፣ በጀትዎ ውስጥ ነው።'
    """
    try:
        response = await model.generate_content(prompt)
        return response.text
    except Exception as e:
        await logger.error("Gemini API failed", error=str(e))
        logger.error("Gemini API failed", error=str(e))
        return f"Reason generation failed in {lang_map[language]}."
