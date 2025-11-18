# AI Recommendation Service API Documentation (Frontend Guide)

This document describes how frontend clients should interact with the AI Recommendation microservice.

Base URL: `http://0.0.0.0:8005`

Authentication: Bearer JWT in `Authorization` header for protected endpoints.

Rate Limiting: `POST /api/v1/recommendations` limited to 5 requests per 60 seconds per client.

---

## Table of Contents
- Authentication
- Healthcheck
- Recommendations
  - Generate Recommendations (POST)
  - Get Saved Recommendations by ID (GET)
  - Get Latest Recommendations for Current User (GET)
  - Get All My Recommendation Logs (GET)
  - Provide Feedback on a Recommendation (POST)
- Schemas
- Error Handling & Status Codes
- Environment & Configuration
- Notes on Transport & Reasoning

---

## Authentication
All endpoints under `/api/v1` require a tenant JWT.

Header:
```
Authorization: Bearer <YOUR_JWT>
```

---

## Healthcheck (No Auth)
GET `/health`

- Purpose: Verify service and DB availability without auth.
- Response:
```
{
  "status": "ok" | "degraded",
  "database": "up" | "down: <error>",
  "config": {
    "db_url_set": true,
    "redis_url_set": true,
    "gebeta_key_set": true,
    "gemini_key_set": true
  },
  "approved_properties_count": 12
}
```

---

## Recommendations

### Generate Recommendations
POST `/api/v1/recommendations`

Headers:
- `Authorization: Bearer <YOUR_JWT>`
- `Content-Type: application/json`

Request Body:
```
{
  "job_school_location": "string",            // e.g., "Bole"
  "salary": number,                           // e.g., 5000
  "house_type": "string",                    // e.g., "apartment" | "house" | "condo" | "private" | ""
  "family_size": number,                      // e.g., 2
  "preferred_amenities": ["string", ...],    // e.g., ["wifi", "parking"]
  "language": "en" | "am" | "or"            // English | Amharic | Afaan Oromo
}
```

Success Response (200):
```
{
  "tenant_preference_id": number,            // use this ID to fetch saved recommendations later
  "recommendations": [RecommendationResponse, ...],
  "total_budget_suggestion": number          // 30% of salary
}
```

Example curl:
```
curl -X POST \
  'http://0.0.0.0:8005/api/v1/recommendations' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR_JWT' \
  -H 'Content-Type: application/json' \
  -d '{
    "job_school_location": "Bole",
    "salary": 5000,
    "house_type": "apartment",
    "family_size": 2,
    "preferred_amenities": ["wifi","parking"],
    "language": "am"
  }'
```

Notes:
- The service queries the `properties` table directly and only returns `status='APPROVED'`.
- Multiple DB fallbacks are used to avoid empty results.

---

### Get Saved Recommendations by ID
GET `/api/v1/recommendations/{tenant_preference_id}`

- Path Param: `tenant_preference_id` (number) — returned by the POST call above.
- Headers: `Authorization: Bearer <YOUR_JWT>`

Response (200):
```
[RecommendationResponse, ...]
```

If the ID has no saved logs, returns `[]`.

---

### Get Latest Recommendations for Current User
GET `/api/v1/recommendations/latest`

- Headers: `Authorization: Bearer <YOUR_JWT>`
- Response (200):
```
[RecommendationResponse, ...]
```

If the current user has no saved logs, returns `[]`.

---

### Get All My Recommendation Logs
GET `/api/v1/recommendations/mine`

- Headers: `Authorization: Bearer <YOUR_JWT>`
- Response (200):
```
[
  {
    "tenant_preference_id": number,
    "created_at": "ISO-8601",
    "recommendations": [RecommendationResponse, ...]
  },
  ...
]
```

---

### Provide Feedback on a Recommendation
POST `/api/v1/recommendations/feedback`

Headers:
- `Authorization: Bearer <YOUR_JWT>`
- `Content-Type: application/json`

Body:
```
{
  "tenant_preference_id": number,         // the preference id you got from POST
  "property_id": "string",               // UUID of the recommended property
  "liked": true | false,                  // whether you liked the recommendation
  "note": "string"                       // optional comment
}
```

Response (200):
```
{"message": "Feedback recorded"}
```

---

## Schemas

### RecommendationRequest
```
{
  job_school_location: string,
  salary: number,
  house_type: string,
  family_size: number,
  preferred_amenities: string[],
  language: "en" | "am" | "or"
}
```

### RecommendationResponse
```
{
  property_id: string,             // UUID string
  title: string,
  location: string,
  price: number,
  transport_cost: number,          // monthly transport estimate
  affordability_score: number,     // higher is better (relative to salary budget)
  reason: string,                  // 3 numbered lines (Fit, Family/Home, Value)
  map_url: string,
  images?: string[],
  details?: {
    bedrooms?: number | null,
    house_type?: string,
    amenities?: string[],
    location?: string
  },
  route?: {
    source?: string,
    destination?: string,
    distance_km?: number,
    fare?: number,
    monthly_cost?: number
  },
  reason_details?: {
    distance_km?: number,
    single_trip_fare?: number,
    monthly_transport_cost?: number,
    rent_price?: number,
    salary?: number,
    budget_30_percent?: number,
    remaining_after_rent_transport?: number,
    family_size?: number,
    bedrooms?: number | null,
    amenities?: string[],
    house_type?: string
  }
}
```

---

## Error Handling & Status Codes
- 200 OK — Success
- 401 Unauthorized — Missing/invalid JWT
- 403 Forbidden — Role not permitted (must be `tenant`)
- 422 Unprocessable Entity — Validation error (check request schema)
- 429 Too Many Requests — Rate limit exceeded on POST /recommendations
- 500 Internal Server Error — Unexpected server error

---

## Environment & Configuration
- `.env` (not checked in):
  - `DATABASE_URL` — Postgres connection string
  - `GEBETA_API_KEY` — Gebeta Maps API key
  - `GEMINI_API_KEY` — Google Gemini API key
  - `REDIS_URL` — Redis URL for rate limiting
- The service reads these values via `app/config.py`.

---

## Notes on Transport & Reasoning
- Distances computed via Gebeta ONM API; coordinates validated and sanitized.
- If ONM fails, the system uses a fallback transport estimate.
- Reason text is generated by Gemini in English/Amharic/Afaan Oromo and follows a strict 3-line priority format:
  1) Fit: proximity and affordability vs 30% salary
  2) Family/Home: fit vs family size, house type, key amenity
  3) Value: remaining budget after rent + transport

---

## Quick Testing Cheatsheet

- Health:
```
curl -s http://0.0.0.0:8005/health | jq
```

- Generate:
```
curl -X POST http://0.0.0.0:8005/api/v1/recommendations \
 -H 'Authorization: Bearer YOUR_JWT' \
 -H 'Content-Type: application/json' \
 -d '{"job_school_location":"Bole","salary":5000,"house_type":"apartment","family_size":2,"preferred_amenities":["wifi","parking"],"language":"am"}'
```

- Latest:
```
curl -X GET http://0.0.0.0:8005/api/v1/recommendations/latest \
 -H 'Authorization: Bearer YOUR_JWT'
```

- Mine:
```
curl -X GET http://0.0.0.0:8005/api/v1/recommendations/mine \
 -H 'Authorization: Bearer YOUR_JWT'
```

- By ID:
```
curl -X GET http://0.0.0.0:8005/api/v1/recommendations/<<TENANT_PREFERENCE_ID>> \
 -H 'Authorization: Bearer YOUR_JWT'
```

---

## Frontend Integration Snippets

Below are minimal client examples to integrate quickly.

### JavaScript (fetch)
```js
const BASE = 'http://0.0.0.0:8005';
const token = 'YOUR_JWT';

async function getLatest() {
  const res = await fetch(`${BASE}/api/v1/recommendations/latest`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function generate(payload) {
  const res = await fetch(`${BASE}/api/v1/recommendations`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// Example usage
(async () => {
  const body = {
    job_school_location: 'Bole',
    salary: 5000,
    house_type: 'apartment',
    family_size: 2,
    preferred_amenities: ['wifi','parking'],
    language: 'am',
  };
  const { tenant_preference_id, recommendations } = await generate(body);
  console.log('Saved ID:', tenant_preference_id, recommendations);
  const latest = await getLatest();
  console.log('Latest:', latest);
})();
```

### TypeScript (Axios)
```ts
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://0.0.0.0:8005',
  headers: { Authorization: `Bearer ${process.env.NEXT_PUBLIC_JWT}` },
});

type RecommendationRequest = {
  job_school_location: string;
  salary: number;
  house_type: string;
  family_size: number;
  preferred_amenities: string[];
  language: 'en' | 'am' | 'or';
};

export async function generateRecommendations(req: RecommendationRequest) {
  const { data } = await api.post('/api/v1/recommendations', req);
  return data as {
    tenant_preference_id: number;
    recommendations: any[];
    total_budget_suggestion: number;
  };
}

export async function getLatestRecommendations() {
  const { data } = await api.get('/api/v1/recommendations/latest');
  return data as any[];
}

export async function sendFeedback(payload: {
  tenant_preference_id: number;
  property_id: string;
  liked: boolean;
  note?: string;
}) {
  const { data } = await api.post('/api/v1/recommendations/feedback', payload);
  return data as { message: string };
}
```

### Common error patterns
- 401 Unauthorized: missing/invalid JWT.
- 403 Forbidden: role must be `tenant`.
- 422 Unprocessable Entity: validation error (check body shape or path params). If calling `/latest` or `/mine`, ensure server is restarted with the latest route order.
- 429 Too Many Requests: hit rate limit on POST `/recommendations`.
- 500: unexpected server error — check server logs.

### CORS & Rate Limits
- Allowed origins (default): `https://*.huggingface.co`, `https://*.vercel.app`. Update `app/main.py` if your frontend uses another domain.
- Rate limiting on `POST /api/v1/recommendations`: 5 requests per 60s.

