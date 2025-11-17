# AI Recommendation Microservice

This microservice provides intelligent property recommendations for tenants within a rental management system, focusing on Ethiopia-specific needs. It leverages FastAPI, PostgreSQL, LangGraph, LangChain, ChromaDB, and Gemini 2.0 Flash to deliver personalized, secure, and scalable recommendations.

## Features

- **Personalized Recommendations**: Recommends properties based on tenant's job/school location, salary, house type, family size, and preferred amenities.
- **Ethiopia-Specific**: Supports Amharic/Afaan Oromo inputs, uses Gebeta Maps for geocoding and minibus route cost estimation.
- **Smart Agent**: Utilizes LangGraph for orchestrating the recommendation workflow, including conditional edges, fallback mechanisms, and feedback-driven ranking.
- **RAG with ChromaDB**: Embeds tenant profiles, properties, and transport data for precise retrieval-augmented generation.
- **Zero-Cost Deployment**: Designed for deployment on Hugging Face Spaces (free tier) with Gemini 2.0 Flash (free tier) and Gebeta Maps (free tier).
- **Secure & Scalable**: Implements JWT authentication, rate limiting, HTTPS, Redis caching, and async queries.
- **Relational Database Integration**: Integrates `TenantProfiles` and `RecommendationLogs` with pre-existing `Users` and `Properties` tables via foreign keys.

## Folder Structure

```
ai_recommendation/
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── requirements.txt
├── train_data/
│   └── transport_price_data.json
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 2025_11_10_create_tenant_profiles_recommendation_logs.py
├── sql/
│   └── seed.sql
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── core/
│   │   └── logging.py
│   ├── dependencies/
│   │   └── auth.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── tenant_profile.py
│   ├── routers/
│   │   └── recommendation.py
│   ├── schemas/
│   │   └── recommendation.py
│   ├── services/
│   │   ├── gebeta.py
│   │   ├── gemini.py
│   │   ├── langgraph_agent.py
│   │   ├── rag.py
│   │   └── search.py
│   └── utils/
│       └── retry.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_recommendation.py
├── alembic.ini
└── migrate.sh
```

## Setup

### 1. Clone the repository

```bash
git clone <repository_url>
cd ai_recommendation
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the root directory based on `.env.example` and fill in the values:

```
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/rental_db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your_jwt_secret
GEBETA_API_KEY=your_gebeta_key
GEMINI_API_KEY=your_gemini_key
USER_MANAGEMENT_URL=http://user-management:8000
SEARCH_FILTERS_URL=http://search-filters:8000
```

- **`DATABASE_URL`**: Connection string for your PostgreSQL database.
- **`REDIS_URL`**: Connection string for your Redis instance (for caching and rate limiting).
- **`JWT_SECRET`**: A strong secret key for JWT authentication.
- **`GEBETA_API_KEY`**: Obtain from [Gebeta Maps](https://gebeta.app/register).
- **`GEMINI_API_KEY`**: Obtain from [Google AI Studio](https://makersuite.google.com/app/apikey).
- **`USER_MANAGEMENT_URL`**: URL of the User Management Microservice.
- **`SEARCH_FILTERS_URL`**: URL of the Search & Filters Microservice.

### 4. Run Migrations and Seed Data

Initialize Alembic and apply migrations:

```bash
alembic init alembic
./migrate.sh
```

**Note**: Ensure your PostgreSQL database is running and accessible before running migrations. The `migrate.sh` script also seeds initial data into `Users`, `Properties`, and `TenantProfiles` tables.

### 5. Initialize ChromaDB

The `setup_vector_store` function in `app/services/rag.py` needs to be called to initialize ChromaDB with property and transport data. This can be done as part of your application startup or as a separate script.

### 6. Run the Application Locally

```bash
uvicorn app.main:app --host 0.0.0.0 --port 7860
```

The API documentation will be available at `http://localhost:7860/docs`.

## Endpoints

### `POST /api/v1/recommendations`

Get personalized property recommendations.

- **Input**:
  ```json
  {
      "job_school_location": "Bole",
      "salary": 5000.0,
      "house_type": "apartment",
      "family_size": 2,
      "preferred_amenities": ["wifi", "parking"],
      "language": "am"
  }
  ```
- **Headers**: `Authorization: Bearer <your_tenant_jwt_token>`
- **Output**:
  ```json
  {
      "recommendations": [
          {
              "property_id": 1,
              "title": "Apartment in Bole",
              "location": "Bole, Addis Ababa",
              "price": 1500.0,
              "transport_cost": 50.0,
              "affordability_score": 0.5,
              "reason": "ይህ አፓርትመንት በቦሌ ከሥራዎ 5 ኪ.ሜ ርቀት ላይ ነው፣ ወርሃዊ ትራንስፖርት 50 ብር፣ በጀትዎ ውስጥ ነው።",
              "map_url": "https://api.gebeta.app/tiles/9.0/38.7/15"
          }
      ],
      "total_budget_suggestion": 1500.0
  }
  ```

### `GET /api/v1/recommendations/{tenant_id}`

Fetch saved recommendations for a specific tenant.

- **Headers**: `Authorization: Bearer <your_tenant_jwt_token>`
- **Output**: List of `RecommendationResponse` objects.

### `POST /api/v1/recommendations/feedback`

Log feedback on recommendations to adjust ranking weights.

- **Input**:
  ```json
  {
      "tenant_id": 1,
      "property_id": 1,
      "liked": true
  }
  ```
- **Headers**: `Authorization: Bearer <your_tenant_jwt_token>`
- **Output**: `{"message": "Feedback recorded"}`

## Testing

To run tests:

```bash
pytest tests/
```

## Deployment on Hugging Face Spaces

1. **Create a new Space**: Choose "Docker" as the Space SDK.
2. **Push your code**: Upload your project files to the Space's Git repository.
3. **Configure Secrets**: In the Space settings, add your environment variables (e.g., `DATABASE_URL`, `GEMINI_API_KEY`) as Space Secrets.
4. **Persistent Storage**: Ensure your Space is configured with persistent storage for ChromaDB (e.g., `/persistent-storage`).
5. **Build and Deploy**: Hugging Face will automatically build and deploy your Docker image using the provided `Dockerfile`. The application will be accessible on port `7860`.

## Contributing

Please read `CONTRIBUTING.md` for details on our code of conduct, and the process for submitting pull requests to us.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
