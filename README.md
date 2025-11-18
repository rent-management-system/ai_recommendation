# AI Recommendation Microservice

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub Workflow Status](https://img.shields.io/badge/Workflow-Passing-brightgreen)](https://github.com/rent-management-system/ai_recommendation/actions/workflows/main.yml)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.103.0-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-336791.svg)](https://www.postgresql.org/)

## Table of Contents

- [AI Recommendation Microservice](#ai-recommendation-microservice)
  - [Table of Contents](#table-of-contents)
  - [1. Overview](#1-overview)
  - [2. Features](#2-features)
  - [3. Technologies Used](#3-technologies-used)
  - [4. Architecture Diagram](#4-architecture-diagram)
  - [5. Folder Structure](#5-folder-structure)
  - [6. Setup Guide](#6-setup-guide)
    - [6.1. Prerequisites](#61-prerequisites)
    - [6.2. Clone the Repository](#62-clone-the-repository)
    - [6.3. Create Virtual Environment and Install Dependencies](#63-create-virtual-environment-and-install-dependencies)
    - [6.4. Environment Variables](#64-environment-variables)
    - [6.5. Database Setup (Migrations and Seeding)](#65-database-setup-migrations-and-seeding)
    - [6.6. ChromaDB Initialization](#66-chromadb-initialization)
    - [6.7. Running the Application Locally](#67-running-the-application-locally)
  - [7. API Endpoints](#7-api-endpoints)
    - [7.1. `POST /api/v1/recommendations`](#71-post-apiv1recommendations)
    - [7.2. `GET /api/v1/recommendations/{tenant_preference_id}`](#72-get-apiv1recommendationstenant_preference_id)
    - [7.3. `POST /api/v1/recommendations/feedback`](#73-post-apiv1recommendationsfeedback)
    - [7.4. `POST /api/v1/properties/search`](#74-post-apiv1propertiessearch)
  - [8. Testing](#8-testing)
  - [9. Deployment on Hugging Face Spaces](#9-deployment-on-hugging-face-spaces)
  - [10. Contributing](#10-contributing)
  - [11. License](#11-license)
  - [12. Contact Information](#12-contact-information)

---

## 1. Overview

The AI Recommendation Microservice is a specialized component within a larger rental management system, designed to provide intelligent and personalized property recommendations to tenants. This service is tailored for Ethiopia-specific needs, incorporating local geographical data and language support. It leverages advanced AI techniques, including large language models (LLMs) and retrieval-augmented generation (RAG), orchestrated by LangGraph, to deliver highly relevant and context-aware suggestions.

The core objective is to enhance the tenant's property search experience by considering various factors such as job/school location, salary, preferred house type, family size, and amenities, ultimately suggesting properties that align with their lifestyle and budget.

## 2. Features

*   **Personalized Property Recommendations**: Generates property recommendations based on a comprehensive tenant profile, including job/school location, salary, house type, family size, and preferred amenities.
*   **Ethiopia-Specific Context**: Integrates deeply with **Gebeta Maps** for accurate, local-context geocoding and precise minibus route cost estimations within Ethiopia. This ensures recommendations are highly relevant to the local transport and geographical landscape. Supports Amharic and Afaan Oromo inputs and outputs for enhanced local relevance.
*   **Intelligent Agent Orchestration (LangGraph)**: Utilizes LangGraph to build a robust and flexible recommendation workflow, incorporating conditional logic, fallback mechanisms, and feedback loops to continuously refine recommendations.
*   **Retrieval-Augmented Generation (RAG) with ChromaDB**: Embeds tenant profiles, property listings, and transport data into ChromaDB, enabling efficient retrieval of relevant information to augment LLM-generated recommendations.
*   **Zero-Cost Deployment Focus**: Designed with an emphasis on cost-effective deployment, leveraging platforms like Hugging Face Spaces (free tier) and Google Gemini 2.0 Flash (free tier), along with Gebeta Maps (free tier).
*   **Secure & Scalable Architecture**: Implements JWT authentication for secure access, rate limiting to prevent abuse, HTTPS for encrypted communication, Redis for caching and session management, and asynchronous queries for high performance.
*   **Relational Database Integration**: Seamlessly integrates with existing `Users` and `Properties` tables via foreign keys, managing `TenantPreferences` and `RecommendationLogs` within a PostgreSQL database.
*   **Dynamic Property Search**: Provides an endpoint for natural language property search, converting user queries into SQL for flexible and powerful filtering.

## 3. Technologies Used

This microservice is built using a modern Python-based stack, incorporating various libraries and frameworks for AI, data management, and API development:

*   **Backend Framework**: `FastAPI` (0.103.0) - High-performance, easy-to-use web framework for building APIs.
*   **Asynchronous Web Server**: `Uvicorn` (0.23.2) - ASGI server for FastAPI.
*   **Database**: `PostgreSQL` - Robust relational database.
*   **Asynchronous ORM**: `SQLAlchemy` (2.0.20) with `asyncpg` (0.28.0) - Asynchronous database toolkit and ORM.
*   **Database Migrations**: `Alembic` (1.12.0) - Database migration tool for SQLAlchemy.
*   **Data Validation**: `Pydantic` - Data validation and settings management using Python type hints.
*   **LLM Integration**: `google-generativeai` (0.3.0) - Python client for Google Gemini API.
*   **AI Orchestration**: `LangGraph` (1.0.2) - Library for building stateful, multi-actor applications with LLMs.
*   **Vector Database**: `ChromaDB` (1.3.4) - Open-source embedding database for RAG.
*   **Embeddings**: `sentence-transformers` (2.2.2) - For generating embeddings from text.
*   **HTTP Client**: `Httpx` (0.28.1) - Fully featured HTTP client for Python.
*   **Authentication**: `python-jose[cryptography]` (3.3.0) - JOSE (JSON Object Signing and Encryption) implementation.
*   **Caching/Rate Limiting**: `Redis` (4.5.0) with `fastapi-limiter` (0.1.5) - In-memory data store for caching and rate limiting.
*   **Structured Logging**: `Structlog` (23.1.0) - Modern logging library.
*   **Retry Mechanism**: `Tenacity` (8.2.3) - General-purpose retrying library.
*   **Circuit Breaker**: `Pybreaker` (1.0.2) - Implementation of the Circuit Breaker pattern.
*   **Data Manipulation**: `Pandas` (2.0.3) - Data analysis and manipulation library.
*   **Testing**: `Pytest` (7.4.0) with `pytest-asyncio` (0.21.1) - Testing framework for Python.
*   **Environment Management**: `python-dotenv` - Reads key-value pairs from a `.env` file.

## 4. Architecture Diagram

The AI Recommendation Microservice operates within a broader ecosystem, interacting with several other services and external APIs. Below is a conceptual overview of its architecture:

```mermaid
graph TD
    A[Client Application] --> B(FastAPI Recommendation Service);
    B --> C(User Management Microservice);
    B --> D(Gebeta Maps API);
    B --> E(Search & Filters Microservice);
    B --> F(Google Gemini API);
    B --> G(PostgreSQL Database);
    B --> H(Redis);
    B --> I(ChromaDB);

    subgraph Recommendation Workflow
        B -- LangGraph Agent --> J(Geocoding);
        J --> K(Property Search);
        K --> L(Transport Cost);
        L --> M(Ranking);
        M --> N(Reason Generation);
        N --> O(Log & Return);
    end
```

**Explanation of Components:**

*   **Client Application**: Represents any frontend application (web, mobile) that consumes the recommendation service.
*   **FastAPI Recommendation Service**: The core microservice, handling API requests, orchestrating the recommendation logic, and interacting with other services.
*   **User Management Microservice**: An external service responsible for user authentication and authorization. The Recommendation Service verifies JWT tokens with this service.
*   **Gebeta Maps API**: An external geospatial service used for geocoding locations (converting addresses to coordinates) and calculating transport costs/distances.
*   **Search & Filters Microservice**: An external service responsible for querying and filtering property listings based on various criteria.
*   **Google Gemini API**: An external Large Language Model (LLM) used for generating human-readable reasons and justifications for property recommendations.
*   **PostgreSQL Database**: The primary data store for the microservice, storing `TenantPreferences`, `RecommendationLogs`, and interacting with `Users` and `Properties` tables.
*   **Redis**: Used for caching frequently accessed data and implementing rate limiting to protect the API from abuse.
*   **ChromaDB**: A local vector database used for Retrieval-Augmented Generation (RAG). It stores embeddings of property data and transport information, allowing for semantic search and context retrieval.
*   **Recommendation Workflow (LangGraph Agent)**: This is the internal orchestration logic within the FastAPI service, implemented using LangGraph. It's a stateful agent that guides the recommendation process through several steps:
    *   **Geocoding Step**: Determines the coordinates of the tenant's job/school location. It first attempts to infer coordinates from local transport data (`train_data/transport_price_data.json`) for better local accuracy. If not found, it uses fallback coordinates (currently 9.0, 38.7 for Addis Ababa).
    *   **Property Search Step**: Queries for potential properties based on tenant preferences. This step employs a multi-stage search strategy to ensure a sufficient number of relevant properties are found:
        1.  **Primary Search**: Narrows down properties based on location, a tight price range (20-30% of salary), house type, bedrooms, and preferred amenities. Properties must have an `APPROVED` status.
        2.  **Fallback 1 (Broaden Filters)**: If the primary search yields fewer than 3 results, it broadens the price range (10-50% of salary) and relaxes house type, bedrooms, and amenities filters. Still requires `APPROVED` status.
        3.  **Fallback 2 (DB-level Query)**: If still insufficient, it performs a direct SQL query to the PostgreSQL database, searching within a wider price range (10-60% of salary) and location (using `ILIKE`), ordered randomly. Only `APPROVED` properties are considered.
        4.  **Fallback 3 (DB Wide Query)**: If necessary, it searches for any `APPROVED` properties within an even wider price range (10-70% of salary), ignoring location, ordered randomly.
        5.  **Fallback 4 (Any Approved)**: As a last resort, it fetches any `APPROVED` properties, ordered randomly, to ensure some recommendations are always provided.
        The goal is to always return up to 10 relevant properties for further processing.
    *   **Transport Cost Calculation Step**: Estimates the monthly transport cost from the tenant's job/school location to each potential property. It uses Gebeta Maps API (`get_matrix`) for distance matrix calculations and local transport price data (`train_data/transport_price_data.json`) to estimate fares. If Gebeta Maps fails or no direct route is found, it attempts nearest-route matching using Haversine distance on coordinates. If all else fails, it uses fallback fares (e.g., 50 ETB/month).
    *   **Ranking Step**: This is where the top recommendations are determined based on a weighted scoring system:
        *   **Initial Weights**: Properties are initially ranked based on a weighted combination of `proximity` (0.4), `affordability` (0.3), and `family_fit` (0.3).
        *   **Feedback Adjustment**: The weights are dynamically adjusted based on historical user feedback stored in `RecommendationLogs`. If a tenant has previously "liked" recommendations, the `proximity` weight is slightly increased (+0.1), and `affordability` and `family_fit` weights are slightly decreased (-0.05 each). This allows the system to adapt to individual tenant preferences over time.
        *   **Sorting Logic**: Properties are sorted by a calculated score. The score is lower for better matches. The formula used is:
            `score = (distance_km * proximity_weight) + (property_price / tenant_salary * affordability_weight) + (abs(property_bedrooms - tenant_family_size) * family_fit_weight)`
            -   `distance_km`: Distance from job/school to property. Lower is better.
            -   `property_price / tenant_salary`: Rent-to-salary ratio. Lower is better.
            -   `abs(property_bedrooms - tenant_family_size)`: Absolute difference between property bedrooms and family size. Lower is better.
        *   **Selection**: The top 3 ranked properties (or fewer if fewer are available) are selected as the final recommendations.
    *   **Reason Generation Step**: Uses the Google Gemini API (`generate_reason`) to generate a concise, user-friendly justification for each of the top recommendations. The prompt provided to Gemini is rich with context, including the tenant's profile, property details, transport costs, and other relevant information (distance, monthly transport cost, single trip fare, rent price, salary, family size, bedrooms, amenities, house type). The reason is generated in the tenant's preferred language (English, Amharic, or Afaan Oromo).
    *   **Log & Return Recommendations**: Saves the final generated recommendations and any associated feedback to the `RecommendationLogs` table in PostgreSQL and returns the top recommendations to the client.

## 5. Folder Structure

```
ai_recommendation/
├── .env.example                 # Example environment variables file
├── .gitignore                   # Git ignore rules
├── alembic.ini                  # Alembic configuration for database migrations
├── Dockerfile                   # Dockerfile for containerization
├── migrate.sh                   # Script to run Alembic migrations and seed data
├── README.md                    # Project README file
├── requirements.txt             # Python dependencies
├── train_data/
│   └── transport_price_data.json # Training data for transport prices
├── alembic/                     # Alembic migration scripts
│   ├── env.py                   # Alembic environment configuration
│   ├── script.py.mako           # Mako template for new migration scripts
│   └── versions/                # Directory for migration version files
│       └── fae2c32ac672_initial_clean_migration.py # Initial database schema migration
├── sql/
│   └── seed.sql                 # SQL script for seeding initial data
├── app/                         # Main application source code
│   ├── __init__.py              # Makes 'app' a Python package
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Application settings and configuration
│   ├── core/
│   │   └── logging.py           # Structured logging configuration
│   ├── dependencies/
│   │   └── auth.py              # Authentication dependency for FastAPI
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── __init__.py          # Exports all models
│   │   ├── password_reset.py    # Password reset token model
│   │   ├── payment.py           # Payment model
│   │   ├── property.py          # Property model (external, but referenced)
│   │   ├── refresh_token.py     # Refresh token model
│   │   ├── saved_search.py      # Saved search model
│   │   ├── tenant_profile.py    # Tenant preference and recommendation log models
│   │   └── user.py              # User model (external, but referenced)
│   ├── routers/                 # FastAPI route definitions
│   │   └── recommendation.py    # Recommendation-related API endpoints
│   ├── schemas/                 # Pydantic schemas for request/response validation
│   │   ├── property_search.py   # Schemas for property search requests/responses
│   │   └── recommendation.py    # Schemas for recommendation requests/responses
│   ├── services/                # Business logic and external service integrations
│   │   ├── gebeta.py            # Gebeta Maps API integration
│   │   ├── gemini.py            # Google Gemini API integration
│   │   ├── langgraph_agent.py   # LangGraph agent for recommendation workflow
│   │   ├── property_search.py   # Service for natural language property search
│   │   ├── rag.py               # Retrieval-Augmented Generation (RAG) logic with ChromaDB
│   │   └── search.py            # External Search & Filters microservice integration
│   └── utils/
│       └── retry.py             # Utility for API call retries
└── tests/                       # Unit and integration tests
    ├── __init__.py              # Makes 'tests' a Python package
    ├── conftest.py              # Pytest fixtures and configurations
    └── test_recommendation.py   # Tests for recommendation endpoints and logic
```

## 6. Database Schema and Design

The microservice interacts with several PostgreSQL tables, some of which are managed directly by this service (`TenantPreferences`, `RecommendationLogs`) and others are external but referenced (`users`, `properties`, `payments`, `refresh_tokens`, `password_resets`, `SavedSearches`). The design emphasizes clear relationships, efficient data storage, and scalability.

### Key Tables and Relationships:

*   **`users` (External)**:
    *   **Purpose**: Stores user authentication and profile information.
    *   **Key Fields**: `id` (UUID, Primary Key), `email`, `full_name`, `role` (Enum: `admin`, `owner`, `tenant`, `broker`).
    *   **Relationship**: One-to-many with `TenantPreferences` (a user can have many preferences), `properties` (a user can own many properties), `payments`, `refresh_tokens`, `password_resets`, and `SavedSearches`.
*   **`properties` (External)**:
    *   **Purpose**: Stores details about rental properties.
    *   **Key Fields**: `id` (UUID, Primary Key), `user_id` (Foreign Key to `users.id`), `title`, `description`, `location`, `price`, `house_type`, `amenities` (JSONB), `photos` (JSONB), `lat`, `lon`, `status`.
    *   **Relationship**: One-to-many with `payments` (a property can have many payments), and referenced by `TenantPreferences` indirectly through recommendations.
*   **`TenantPreferences` (Managed by this service)**:
    *   **Purpose**: Stores a tenant's specific preferences used to generate recommendations.
    *   **Key Fields**: `id` (Integer, Primary Key, auto-increment), `user_id` (UUID, Foreign Key to `users.id`), `job_school_location`, `salary`, `house_type`, `family_size`, `preferred_amenities` (ARRAY of String), `created_at`.
    *   **Relationship**: One-to-many with `RecommendationLogs` (one preference can lead to many recommendation logs).
*   **`RecommendationLogs` (Managed by this service)**:
    *   **Purpose**: Stores generated recommendations and user feedback for historical tracking and future model refinement.
    *   **Key Fields**: `id` (Integer, Primary Key), `tenant_preference_id` (Foreign Key to `TenantPreferences.id`), `recommendation` (JSONB), `feedback` (JSONB), `created_at`.
    *   **Relationship**: Many-to-one with `TenantPreferences`.
*   **`payments` (External)**:
    *   **Purpose**: Tracks payment transactions related to properties.
    *   **Key Fields**: `id` (UUID, Primary Key), `property_id` (Foreign Key to `properties.id`), `user_id` (Foreign Key to `users.id`), `amount`, `status`.
*   **`refresh_tokens` (External)**:
    *   **Purpose**: Stores refresh tokens for user authentication.
    *   **Key Fields**: `id` (UUID, Primary Key), `user_id` (Foreign Key to `users.id`), `token`, `expires_at`.
*   **`password_resets` (External)**:
    *   **Purpose**: Stores tokens for password reset functionality.
    *   **Key Fields**: `id` (UUID, Primary Key), `user_id` (Foreign Key to `users.id`), `token`, `expires_at`.
*   **`SavedSearches` (External)**:
    *   **Purpose**: Allows users to save their property search criteria.
    *   **Key Fields**: `id` (Integer, Primary Key), `user_id` (Foreign Key to `users.id`), `location`, `min_price`, `max_price`, `house_type`, `amenities`, `bedrooms`.

### Design Considerations:

*   **UUID for External IDs**: `user_id` and `property_id` use UUIDs, ensuring global uniqueness and preventing ID collisions across microservices.
*   **JSONB for Flexible Data**: `amenities` and `photos` in `properties`, and `recommendation` and `feedback` in `RecommendationLogs` utilize PostgreSQL's `JSONB` type. This provides schema flexibility for semi-structured data, allowing for easy storage and querying of complex objects without rigid schema migrations.
*   **Foreign Key Constraints**: `ON DELETE CASCADE` is used for `TenantPreferences.user_id` and `RecommendationLogs.tenant_preference_id` to ensure data integrity; when a user or tenant preference is deleted, associated records are automatically removed.
*   **Asynchronous Operations**: The service is built with `asyncpg` and `SQLAlchemy`'s async capabilities to handle database operations non-blockingly, improving concurrency and responsiveness.



Follow these steps to set up and run the AI Recommendation Microservice locally.

### 6.1. Prerequisites

Before you begin, ensure you have the following installed:

*   **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
*   **Poetry**: (Recommended for dependency management) `pip install poetry`
*   **Docker & Docker Compose**: (Optional, but recommended for database and Redis) [Install Docker](https://docs.docker.com/get-docker/)
*   **PostgreSQL Database**: A running PostgreSQL instance.
*   **Redis Instance**: A running Redis instance.
*   **API Keys**:
    *   **Gebeta Maps API Key**: Obtain from [Gebeta Maps](https://gebeta.app/register).
    *   **Google Gemini API Key**: Obtain from [Google AI Studio](https://makersuite.google.com/app/apikey).

### 6.2. Clone the Repository

```bash
git clone https://github.com/rent-management-system/ai_recommendation.git
cd ai_recommendation
```

### 6.3. Create Virtual Environment and Install Dependencies

Using `pip` and `venv`:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 6.4. Environment Variables

Create a `.env` file in the root directory of the project based on `.env.example`. Fill in the values with your specific configurations:

```ini
# .env file example
DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/rental_db"
REDIS_URL="redis://localhost:6379/0"
JWT_SECRET="your_super_secret_jwt_key_here_replace_with_a_strong_one"
GEBETA_API_KEY="your_gebeta_api_key"
GEMINI_API_KEY="your_gemini_api_key"
USER_MANAGEMENT_URL="https://rent-managment-system-user-magt.onrender.com" # Example URL, replace with actual
SEARCH_FILTERS_URL="http://localhost:8000" # Example URL, replace with actual
```

**Explanation of Variables:**

*   **`DATABASE_URL`**: The connection string for your PostgreSQL database. Ensure it uses `postgresql+asyncpg` for asynchronous operations.
*   **`REDIS_URL`**: The connection string for your Redis instance, used for caching and rate limiting.
*   **`JWT_SECRET`**: A strong, unique secret key used for signing and verifying JSON Web Tokens (JWTs). **Crucial for security.**
*   **`GEBETA_API_KEY`**: Your API key for accessing the Gebeta Maps service.
*   **`GEMINI_API_KEY`**: Your API key for accessing the Google Gemini API.
*   **`USER_MANAGEMENT_URL`**: The base URL of the User Management Microservice, used for authenticating users.
*   **`SEARCH_FILTERS_URL`**: The base URL of the Search & Filters Microservice, used for retrieving property listings.

### 6.5. Database Setup (Migrations and Seeding)

Ensure your PostgreSQL database is running and accessible. The `migrate.sh` script will apply Alembic migrations and seed initial data.

```bash
chmod +x migrate.sh # Make the script executable
./migrate.sh
```

This script performs the following actions:
1.  Loads environment variables from `.env`.
2.  Runs `alembic upgrade head` to apply all pending database migrations, creating necessary tables like `TenantPreferences` and `RecommendationLogs`.
3.  Converts the `DATABASE_URL` to a synchronous format suitable for `psql`.
4.  Executes `sql/seed.sql` to populate the `users`, `properties`, and `TenantPreferences` tables with initial data.

### 6.6. ChromaDB Initialization

The ChromaDB vector store needs to be initialized with property and transport data. This is typically done as part of the application startup or via a separate script. The `setup_vector_store` function in `app/services/rag.py` handles this. For local development, you might need to call this function explicitly or ensure it runs on application startup.

The `setup_vector_store` function persists the ChromaDB to `/persistent-storage/chroma_db`. Ensure this directory is writable or adjust the `persist_directory` path as needed for your environment.

### 6.7. Running the Application Locally

Once all dependencies are installed and environment variables are set, you can start the FastAPI application:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 7860 --reload
```

The API documentation (Swagger UI) will be available at `http://localhost:7860/docs`.

## 7. API Endpoints

This section details the available API endpoints, their functionality, request/response schemas, and example usage.

### 7.1. `POST /api/v1/recommendations`

Get personalized property recommendations for a tenant.

*   **Description**: This endpoint processes a tenant's preferences and generates a list of suitable property recommendations, including transport costs, affordability scores, and a natural language reason for each recommendation.
*   **Permissions**: Authenticated Tenant users only.
*   **Rate Limiting**: 5 requests per 60 seconds.
*   **Method**: `POST`
*   **Path**: `/api/v1/recommendations`
*   **Headers**:
    *   `Authorization`: `Bearer <your_tenant_jwt_token>`
*   **Request Body (`application/json`)**:
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
    *   `job_school_location` (string, required): The tenant's job or school location.
    *   `salary` (float, required): The tenant's monthly salary.
    *   `house_type` (string, required): Preferred house type (e.g., "apartment", "house", "condo").
    *   `family_size` (integer, required): Number of family members.
    *   `preferred_amenities` (array of strings, optional): A list of desired amenities (e.g., "wifi", "parking", "security").
    *   `language` (string, optional, default: "en"): Preferred language for the recommendation reason ("en", "am", "or").
*   **Response Body (`application/json`)**:
    ```json
    {
        "recommendations": [
            {
        "property_id": "uuid-of-property-1",
                "title": "Apartment in Bole",
                "location": "Bole, Addis Ababa",
                "price": 1500.0,
                "transport_cost": 50.0,
                "affordability_score": 0.5,
                "reason": "ይህ አፓርትመንት በቦሌ ከሥራዎ 5 ኪ.ሜ ርቀት ላይ ነው፣ ወርሃዊ ትራንስፖርት 50 ብር፣ በጀትዎ ውስጥ ነው።",
                "map_url": "https://api.gebeta.app/tiles/9.0/38.7/15",
                "images": ["url_to_image1.jpg", "url_to_image2.jpg"],
                "details": {
                    "bedrooms": 2,
                    "house_type": "apartment",
                    "amenities": ["wifi", "parking"],
                    "location": "Bole, Addis Ababa"
                },
                "route": {
                    "source": "Bole",
                    "destination": "Bole, Addis Ababa",
                    "distance_km": 5.0,
                    "fare": 10.0,
                    "monthly_cost": 50.0
                },
                "reason_details": {
                    "distance_km": 5.0,
                    "monthly_transport_cost": 50.0,
                    "single_trip_fare": 10.0,
                    "route_source": "Bole",
                    "route_destination": "Bole, Addis Ababa",
                    "rent_price": 1500.0,
                    "salary": 5000.0,
                    "family_size": 2,
                    "bedrooms": 2,
                    "amenities": ["wifi", "parking"],
                    "house_type": "apartment"
                }
            }
        ],
        "total_budget_suggestion": 1500.0
    }
    ```
    *   `recommendations` (array of objects): List of recommended properties.
        *   `property_id` (string): Unique identifier for the property (UUID).
        *   `title` (string): Title of the property.
        *   `location` (string): Location of the property.
        *   `price` (float): Rental price of the property.
        *   `transport_cost` (float): Estimated monthly transport cost to the property.
        *   `affordability_score` (float): A score indicating how affordable the property is relative to the tenant's salary.
        *   `reason` (string): A natural language explanation for the recommendation.
        *   `map_url` (string): URL to a map showing the property's location.
        *   `images` (array of strings, optional): URLs of property images.
        *   `details` (object, optional): Detailed property attributes.
        *   `route` (object, optional): Details about the estimated transport route.
        *   `reason_details` (object, optional): Contextual data used to generate the reason.
    *   `total_budget_suggestion` (float): A suggestion for the tenant's total monthly budget (e.g., 30% of salary).

### 7.2. `GET /api/v1/recommendations/{tenant_preference_id}`

Fetch saved recommendations for a specific tenant preference.

*   **Description**: Retrieves previously generated and logged recommendations associated with a given tenant preference ID.
*   **Permissions**: Authenticated Tenant users only.
*   **Method**: `GET`
*   **Path**: `/api/v1/recommendations/{tenant_preference_id}`
*   **Path Parameters**:
    *   `tenant_preference_id` (integer, required): The ID of the tenant preference for which to retrieve recommendations.
*   **Headers**:
    *   `Authorization`: `Bearer <your_tenant_jwt_token>`
*   **Response Body (`application/json`)**: A list of `RecommendationResponse` objects, similar to the `recommendations` array in the `POST /api/v1/recommendations` output.

### 7.3. `POST /api/v1/recommendations/feedback`

Log feedback on recommendations to adjust ranking weights.

*   **Description**: Allows tenants to provide feedback (e.g., liking or disliking a recommendation), which can be used to refine future recommendation algorithms and ranking.
*   **Permissions**: Authenticated Tenant users only.
*   **Method**: `POST`
*   **Path**: `/api/v1/recommendations/feedback`
*   **Headers**:
    *   `Authorization`: `Bearer <your_tenant_jwt_token>`
*   **Request Body (`application/json`)**:
    ```json
    {
        "tenant_preference_id": 1,
        "property_id": "uuid-of-property-1",
        "liked": true
    }
    ```
    *   `tenant_preference_id` (integer, required): The ID of the tenant preference associated with the feedback.
    *   `property_id` (string, required): The ID of the property for which feedback is being provided (UUID).
    *   `liked` (boolean, required): `true` if the tenant liked the recommendation, `false` otherwise.
*   **Response Body (`application/json`)**:
    ```json
    {
        "message": "Feedback recorded"
    }
    ```

### 7.4. `POST /api/v1/properties/search`

Search for properties using natural language queries.

*   **Description**: This endpoint allows users to search for properties using natural language. The service translates the natural language query into an SQL query and executes it against the property database.
*   **Permissions**: Authenticated Tenant or Landlord users only.
*   **Method**: `POST`
*   **Path**: `/api/v1/properties/search`
*   **Headers**:
    *   `Authorization`: `Bearer <your_jwt_token>` (for Tenant or Landlord)
*   **Request Body (`application/json`)**:
    ```json
    {
        "query": "apartments in Bole with 2 bedrooms under 2000 ETB"
    }
    ```
    *   `query` (string, required): The natural language search query for properties.
*   **Response Body (`application/json`)**:
    ```json
    {
        "results": [
            {
                "id": "uuid-of-property-1",
                "title": "Modern Apartment",
                "location": "Bole, Addis Ababa",
                "price": 1800.0,
                "house_type": "apartment",
                "bedrooms": 2,
                "amenities": ["wifi", "balcony"],
                "lat": 9.0,
                "lon": 38.7,
                "status": "APPROVED"
            },
            {
                "id": "uuid-of-property-2",
                "title": "Spacious Flat",
                "location": "Bole, Addis Ababa",
                "price": 1950.0,
                "house_type": "apartment",
                "bedrooms": 2,
                "amenities": ["parking"],
                "lat": 9.01,
                "lon": 38.71,
                "status": "APPROVED"
            }
        ]
    }
    ```
    *   `results` (array of objects): A list of property dictionaries matching the search query. The exact fields depend on the property model.

## 8. Testing

To run the automated tests for this microservice, navigate to the root directory of the project and execute the following command:

```bash
pytest tests/
```

This will run all tests defined in the `tests/` directory, ensuring the core functionalities and integrations are working as expected.

## 9. Deployment on Hugging Face Spaces

This microservice is designed for easy deployment on Hugging Face Spaces using Docker.

1.  **Create a new Space**:
    *   Go to [Hugging Face Spaces](https://huggingface.co/spaces).
    *   Click "Create new Space".
    *   Choose "Docker" as the Space SDK.
    *   Select a suitable hardware configuration (e.g., CPU Basic for free tier).
2.  **Push your code**:
    *   Upload your entire project directory to the Space's Git repository. You can do this by cloning the Space's Git repository locally, adding your files, committing, and pushing.
3.  **Configure Secrets**:
    *   In your Space settings on Hugging Face, navigate to "Secrets".
    *   Add your environment variables (e.g., `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `GEBETA_API_KEY`, `GEMINI_API_KEY`, `USER_MANAGEMENT_URL`, `SEARCH_FILTERS_URL`) as Space Secrets. These will be automatically injected into your Docker container at runtime.
4.  **Persistent Storage**:
    *   For ChromaDB to persist its data across restarts, ensure your Space is configured with persistent storage. In the Space settings, you might need to specify a mount path, for example, `/persistent-storage`. The `app/services/rag.py` is configured to use `/persistent-storage/chroma_db` by default.
5.  **Build and Deploy**:
    *   Hugging Face will automatically detect your `Dockerfile`, build the Docker image, and deploy your application.
    *   The application will be accessible on port `7860` within the container, which Hugging Face will expose.

## 10. Contributing

We welcome contributions to the AI Recommendation Microservice! Please read `CONTRIBUTING.md` (if available, otherwise follow standard GitHub practices) for details on our code of conduct, and the process for submitting pull requests.

## 11. License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## 12. Contact Information

For any inquiries or further information, please contact the lead developer:

*   **Developer Name**: Dagmawi Teferi
*   **Email**: dagiteferi2011@gmail.com
*   **Phone**: +251 920362324
*   **GitHub Repository**: [https://github.com/rent-management-system/ai_recommendation](https://github.com/rent-management-system/ai_recommendation)