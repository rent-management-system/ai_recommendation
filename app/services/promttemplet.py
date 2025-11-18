from typing import Any, Dict

LANG_MAP = {"en": "English", "am": "Amharic", "or": "Afaan Oromo"}

def build_reason_prompt(tenant_profile: Dict[str, Any],
                        property: Dict[str, Any],
                        context: Dict[str, Any] | None,
                        language: str) -> str:
    ctx = context or {}
    lang_name = LANG_MAP.get(language, "English")
    # Extract useful fields for a clean prompt
    tp_loc = tenant_profile.get("job_school_location") if isinstance(tenant_profile, dict) else None
    salary = tenant_profile.get("salary") if isinstance(tenant_profile, dict) else None
    fam_size = tenant_profile.get("family_size") if isinstance(tenant_profile, dict) else None

    title = property.get("title")
    price = property.get("price")
    location = property.get("location")
    bedrooms = property.get("bedrooms")
    house_type = property.get("house_type")
    amenities = property.get("amenities", [])

    distance_km = ctx.get("distance_km")
    monthly_cost = ctx.get("monthly_transport_cost")
    single_fare = ctx.get("single_trip_fare")
    route_source = ctx.get("route_source")
    route_dest = ctx.get("route_destination")

    # Language-specific style and very short few-shot examples
    examples = {
        "English": (
            "Style: Friendly, clear, and concise. Use numbers with units."
            "\nExamples:" \
            "\n- 'Close to {tp_loc} (~{distance_km} km), minibus {single_fare} ETB/ride (~{monthly_cost} ETB/month)."
            " Rent {price} ETB fits ~30% of salary; {bedrooms or 'N/A'} BR {house_type} suits {fam_size}-person family; key amenity: {amenities[:1] if amenities else '—'}.'"
        ),
        "Amharic": (
            "ዘይቤ: ግልጽና አጭር፣ ቁጥሮችን ከመለኪያ ጋር ተጠቀም።"
            "\nምሳሌዎች:" \
            "\n- 'ከ{tp_loc} ጋር ቅርብ (~{distance_km} ኪ.ሜ)፣ ሚኒባስ {single_fare} ብር/ጉዞ (~{monthly_cost} ብር/ወር)."
            " ኪራይ {price} ብር የደመወዝ 30% ውስጥ ነው፤ {bedrooms or '—'} መኝታ {house_type} ለ{fam_size} ቤተሰብ ይስማማል፣ ጠቃሚ አማካኝ: {amenities[:1] if amenities else '—'}.'"
        ),
        "Afaan Oromo": (
            "Halluu: Ifaa, gabaabaa. Lakkoofsa fi unkaa ittiin fayyadami."
            "\nFakkeenya:" \
            "\n- '{tp_loc}-tti dhihoo (~{distance_km} km); minibus {single_fare} ETB/daandii (~{monthly_cost} ETB/ji'a)."
            " Kiraayiin {price} ETB %30 mindaa keessatti; {bedrooms or '—'} balbala {house_type} maatii {fam_size}f mijaa'a; faayidaa: {amenities[:1] if amenities else '—'}.'"
        ),
    }

    style_block = examples.get(lang_name, examples["English"])

    # Clear, engineered prompt with guardrails
    prompt = f"""
You are a precise real‑estate assistant. Write ONE short justification in {lang_name} for why the property fits the tenant.

Hard constraints:
- 1–2 sentences only (max ~40 words).
- Use numbers with units (km, ETB). Ground facts on provided fields only; do NOT invent values.
- Consider three factors explicitly: proximity/transport, affordability (~30% of salary), family fit (family size vs bedrooms/house type).
- Prefer one key amenity if available.

Tenant Profile:
- Location: {tp_loc}
- Salary: {salary}
- Family size: {fam_size}

Property:
- Title: {title}
- Location: {location}
- Price: {price}
- House type: {house_type}
- Bedrooms: {bedrooms}
- Amenities: {amenities}

Transport:
- Distance (km): {distance_km}
- Single trip fare (ETB): {single_fare}
- Monthly transport cost (ETB): {monthly_cost}
- Route: {route_source} -> {route_dest}

{style_block}

Now produce the justification in {lang_name}. If any value is missing, omit it rather than guessing.
"""
    return prompt
