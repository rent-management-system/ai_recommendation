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

    # Pull numeric context and round for clean rendering
    def _fmt_num(x, nd=1):
        try:
            return round(float(x), nd)
        except Exception:
            return x
    distance_km = _fmt_num(ctx.get("distance_km"), 1)
    monthly_cost = _fmt_num(ctx.get("monthly_transport_cost"), 0)
    single_fare = _fmt_num(ctx.get("single_trip_fare"), 0)
    budget30 = _fmt_num(ctx.get("budget_30_percent"), 0)
    remaining = _fmt_num(ctx.get("remaining_after_rent_transport"), 0)

    # Language-specific style and very short few-shot examples
    examples = {
        "English": (
            "Style: Friendly, clear, concise. Use numbers with units (km, ETB)."
            "\nOutput pattern (example):"
            "\n1) Fit: ~2.5 km from Bole; transport ~400 ETB/month; rent 1500 ETB ≈ 30% of 5000 ETB."
            "\n2) Family/Home: apartment suits a 2‑person family; amenity: wifi."
            "\n3) Value: after rent+transport ≈ 3500 ETB remains."
        ),
        "Amharic": (
            "ዘይቤ፡ ግልጽና አጭር፣ ቁጥሮችን ከመለኪያ ጋር ተጠቀም።"
            "\nየመውጫ አቀራረብ (ምሳሌ):"
            "\n1) ስለ ጥራት፡ ከቦሌ ግማሽ ኪ.ሜ ያነሰ/ወይም ~2.5 ኪ.ሜ፣ ትራንስፖርት ~400 ብር/ወር፣ ኪራይ 1500 ብር ≈ 30% ከ5000 ብር."
            "\n2) ስለ ቤተሰብ/ቤት፡ 2 ሰው ለሚሆን አፓርታማ ይስማማል፣ አማካኝ፡ wifi."
            "\n3) ስለ እሴት፡ ከኪራይና ትራንስፖርት በኋላ ከ3500 ብር በላይ ይቀራል."
        ),
        "Afaan Oromo": (
            "Halluu: Ifaa, gabaabaa; lakkoofsa fi unkaa fayyadami."
            "\nFakkeenya baafata:"
            "\n1) Walsimuu: ~2.5 km Bole irraa; imala ~400 ETB/ji'a; kiraa 1500 ETB ≈ %30 mindaa 5000 ETB."
            "\n2) Maatii/Mana: apartment maatii nama 2‑f mijaa'a; faayidaa: wifi."
            "\n3) Gatii: booda kiraa+imala ≈ 3500 ETB hafe."
        ),
    }

    style_block = examples.get(lang_name, examples["English"])

    # Clear, engineered prompt with guardrails
    prompt = f"""
You are a precise real‑estate assistant. Write ONE short justification in {lang_name} for why the property fits the tenant, using the numbered priority format.

Hard constraints:
- Up to 3 short lines, numbered 1) 2) 3). Keep each line concise.
- Use numbers with units (km, ETB). Ground facts on provided fields only; do NOT invent values.
- Consider three factors explicitly: proximity/transport, affordability (~30% of salary), family fit (family size vs bedrooms/house type).
- Prefer one key amenity if available.

Tenant Profile:
- Location: {tp_loc}
- Salary: {salary}
- Family size: {fam_size}
- Preferred amenities: {amenities}

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
- Budget 30% of salary (ETB): {budget30}
- Remaining after rent+transport (ETB): {remaining}

{style_block}

Now produce the justification in {lang_name} as three numbered lines:
1) Fit: Use distance_km, monthly_cost, and compare rent_price to budget_30_percent.
2) Family/Home: Use family_size, house_type, bedrooms (if known), and one amenity if available.
3) Value: Use remaining_after_rent_transport (round to nearest 10 ETB if you like).
If any value is missing, omit it rather than guessing. Do not include raw placeholders.
"""
    return prompt
