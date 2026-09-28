🔎 EVOSearch

Understand. Compare. Evolve.

EVOSearch is a full-stack AI-powered platform for understanding how documents and source code change over time.

Instead of treating a document as just a file or code as just text, EVOSearch extracts meaningful information, connects related versions, finds changes, and helps users understand the evolution of a project.

Upload → Understand → Search → Compare → Explain → Evolve

🌟 What is EVOSearch?

Imagine you have:

an old version of a company policy,

a new version of the same policy,

several project documents,

and multiple versions of source code.

Normally, you would have to read everything manually and compare the files yourself.

EVOSearch automates much of that work.

It can:

📄 read and process documents

🔍 search documents using semantic meaning

🧩 extract important claims and requirements

🔄 compare document versions

📈 show how topics evolve over time

💬 answer questions using retrieved evidence

💻 analyze source code

🆚 compare code versions

💥 identify potentially affected code areas

💡 suggest possible improvements

The goal is not simply to provide a chatbot.

The goal is to build an evolution intelligence layer over documents and code.

🚀 Main Features

Feature

What it does

📄 Document Intelligence

Processes PDF, DOCX, TXT, Markdown, CSV, JSON and YAML files

🔍 Semantic Search

Finds relevant information based on meaning rather than exact keywords

🧩 Claim Extraction

Extracts important statements, requirements and topics from documents

🔄 Document Comparison

Detects added, removed, modified and unchanged claims

📈 Evolution Timeline

Shows how topics and requirements change across documents

🗺️ Knowledge Map

Connects topics with the documents in which they appear

💬 AI Assistant

Answers questions using retrieved project evidence

💻 Code Intelligence

Extracts and analyzes source-code entities

🆚 Code Comparison

Compares functions, classes, SQL objects and other code entities

💥 Impact Analysis

Finds potentially affected code references

💡 Improvement Suggestions

Highlights possible code/document improvement areas

🔐 Authentication

Provides signup, login and JWT-based authenticated API access

🐳 Docker Support

Runs the application using Docker Compose

☁️ Public Deployment Ready

Can be deployed using a frontend host + backend service + persistent storage

🧠 How EVOSearch Works

At a high level, EVOSearch follows this pipeline:

                    ┌──────────────────┐

                    │      User        │

                    └────────┬─────────┘

                             │

                             ▼

                ┌────────────────────────┐

                │   React + TypeScript   │

                │       Frontend         │

                └───────────┬────────────┘

                            │ REST API

                            ▼

                ┌────────────────────────┐

                │    FastAPI Backend     │

                └───────────┬────────────┘

                            │

             ┌──────────────┼──────────────┐

             ▼              ▼              ▼

        Documents         Code          Authentication

             │              │              │

             ▼              ▼              ▼

        Extraction      Analysis       JWT + bcrypt

             │              │

             ▼              ▼

         Chunking       Code Entities

             │              │

             ▼              ▼

        Embeddings      Comparison

             │              │

             └───────┬──────┘

                     ▼

              ┌──────────────┐

              │    FAISS     │

              │ Vector Index │

              └──────┬───────┘

                     │

                     ▼

              Semantic Search

                     │

                     ▼

                 RAG / AI

                     │

                     ▼

              Evidence-based

                  Answers

📚 Document Intelligence

EVOSearch supports these document formats:

PDF

DOCX

TXT

Markdown

CSV

JSON

YAML

Document Processing Pipeline

When a document is uploaded, the backend processes it approximately like this:

Upload File

    ↓

Validate File

    ↓

Calculate Checksum

    ↓

Store File

    ↓

Extract Text

    ↓

Split into Chunks

    ↓

Generate Embeddings

    ↓

Store Vectors in FAISS

    ↓

Extract Claims

    ↓

Generate Claim Embeddings

    ↓

Generate Summary / Suggestions

    ↓

Document Ready

This converts an uploaded file into searchable structured knowledge.

Chunking

Documents are divided into smaller pieces so that individual pieces can be embedded and retrieved efficiently.

The current configuration uses:

Chunk size:    220 tokens

Overlap:        40 tokens

The overlap helps preserve context between neighboring chunks.

🔍 Semantic Search

Traditional search mainly looks for matching words.

EVOSearch uses semantic search, meaning that it attempts to retrieve text that is conceptually related to the user's query.

Example:

User query:

"Who can access customer information?"

May retrieve:

"Customer records must only be accessible to authorized personnel."

The exact words are different, but the meaning is related.

Search Flow

User Query

    ↓

Create Query Embedding

    ↓

Search FAISS Vector Index

    ↓

Find Similar Chunks

    ↓

Apply Relevant Metadata / Thresholds

    ↓

Return Evidence

EVOSearch uses:

Sentence Transformer:

all-MiniLM-L6-v2

Embedding size:

384 dimensions

FAISS uses a normalized-vector inner-product approach, which makes the similarity behave approximately like cosine similarity.

💬 AI Assistant / RAG

EVOSearch can use retrieved project information as context for AI-generated answers.

This follows a Retrieval-Augmented Generation (RAG) style workflow:

Question

   ↓

Semantic Retrieval

   ↓

Relevant Document Chunks

   ↓

Build Context

   ↓

LLM

   ↓

Answer + Sources

The important idea is:

The AI should answer from the application's retrieved evidence instead of relying only on general model knowledge.

If the available evidence is insufficient, the system can indicate that there is not enough supporting information.

The LLM layer is optional. EVOSearch also has deterministic fallback behavior for supported features when an LLM provider is not configured.

🔄 Document Evolution & Comparison

EVOSearch is designed to answer questions such as:

What changed between these two document versions?

Instead of comparing only raw text, EVOSearch works with extracted claims.

A claim can contain information such as:

topic

original statement

normalized statement

requirement strength

scope

importance

page information

vector reference

Claims from different document versions can then be semantically aligned.

Change Categories

The comparison system can identify changes such as:

ADDED

REMOVED

MODIFIED

UNCHANGED

REQUIREMENT_STRENGTHENED

REQUIREMENT_WEAKENED

SCOPE_EXPANDED

SCOPE_REDUCED

VALUE_CHANGED

This makes the result easier to understand than a traditional line-by-line diff.

📈 Evolution Timeline & Knowledge Map

Once document claims and topics are available, EVOSearch can show how information changes across versions.

Evolution Timeline

Version 1 ─────── Version 2 ─────── Version 3

   │                  │                  │

   ├─ Topic A         ├─ Topic A         ├─ Topic A

   ├─ Topic B         ├─ Topic C         ├─ Topic C

   └─ Topic C         └─ Topic D         └─ Topic D

Knowledge Map

The knowledge map connects topics with the documents in which they appear.

This helps users understand:

which documents discuss a topic

where a topic first appears

where it changes

which documents are related

💻 Code Intelligence

EVOSearch also analyzes source code.

For Python, the project uses Python's built-in AST (Abstract Syntax Tree) capabilities.

For other supported languages, the system uses best-effort parsing and extraction approaches.

Supported code/data formats include:

Python

JavaScript

TypeScript

Java

C

C++

SQL

HTML

CSS

JSON

YAML

Code Analysis

The system can extract code entities such as:

functions

classes

methods

SQL objects

other identifiable code structures

For SQL, specialized extraction is used for objects such as:

CREATE TABLE

CREATE VIEW

CREATE FUNCTION

CREATE PROCEDURE

🆚 Code Comparison

Code versions can be compared at the entity level.

Instead of only displaying:

- old line

+ new line

EVOSearch can reason about entities such as:

Function A

    ↓

Previous version

    ↓

Current version

    ↓

Modified

    ↓

Explanation / Confidence / Category

Possible results include:

added entities

removed entities

modified entities

unchanged entities

The system can retain previous/current code and an explanation of the detected change.

💥 Impact Analysis

EVOSearch can also perform impact analysis by searching for references to changed code entities.

For example:

Changed Function

      ↓

Search References

      ↓

Potentially Affected Files / Entities

      ↓

Impact Information

This is intended as potential impact analysis.

It is not a complete compiler-level call graph or dependency graph.

🔐 Authentication & Security

EVOSearch includes authentication endpoints and JWT-based authorization.

Authentication Flow

User

  ↓

Signup / Login

  ↓

Password hashed with bcrypt

  ↓

JWT issued

  ↓

Frontend stores authentication token

  ↓

API requests use Bearer token

  ↓

Backend validates token

Main authentication endpoints include:

POST /api/auth/signup

POST /api/auth/login

GET  /api/auth/me

Important security properties

Passwords are hashed using bcrypt.

Authentication uses JWT tokens.

API requests can use Bearer authentication.

Uploaded files are validated.

Upload size is configurable.

Filenames are sanitized.

Uploaded source code is not executed by EVOSearch.

Secrets should be provided through environment variables.

.env files should never be committed to GitHub.

For a public production deployment, authentication, authorization, user/document ownership, rate limiting and secret management should be reviewed and hardened further.

🏗️ Technology Stack

Frontend

React

TypeScript

Vite

Tailwind CSS

React Router

TanStack Query

Backend

Python

FastAPI

Pydantic

Uvicorn

SQLAlchemy

AI / Search

Sentence Transformers

all-MiniLM-L6-v2

FAISS

Optional LLM provider

Retrieval-Augmented Generation

Document Processing

PyMuPDF

python-docx

Python standard-library parsers

Database & Storage

SQLite by default

Filesystem storage for uploads

FAISS persistent vector indexes

📁 Project Structure

A simplified view of the project:

EVOSearch/

│

├── backend/

│   ├── app/

│   │   ├── main.py

│   │   ├── config.py

│   │   ├── database.py

│   │   ├── models.py

│   │   ├── schemas.py

│   │   ├── dependencies.py

│   │   │

│   │   ├── api/

│   │   │   ├── auth.py

│   │   │   ├── documents.py

│   │   │   ├── search.py

│   │   │   ├── chat.py

│   │   │   ├── comparison.py

│   │   │   ├── code.py

│   │   │   ├── timeline.py

│   │   │   └── health.py

│   │   │

│   │   └── services/

│   │       ├── document_service.py

│   │       ├── chunking_service.py

│   │       ├── embedding_service.py

│   │       ├── vector_service.py

│   │       ├── retrieval_service.py

│   │       ├── claim_service.py

│   │       ├── comparison_service.py

│   │       ├── code_analysis_service.py

│   │       ├── code_comparison_service.py

│   │       ├── impact_service.py

│   │       ├── summary_service.py

│   │       ├── recommendation_service.py

│   │       └── llm_service.py

│   │

│   ├── tests/

│   ├── requirements.txt

│   └── .env.example

│

├── frontend/

│   ├── src/

│   │   ├── components/

│   │   ├── pages/

│   │   ├── context/

│   │   ├── types/

│   │   └── ...

│   │

│   ├── package.json

│   └── vite.config.*

│

├── docker-compose.yml

├── .gitignore

└── README.md

⚙️ Environment Configuration

The backend uses environment variables for database, storage, embeddings, LLM and security configuration.

The current example configuration is:

# Database

DATABASE_URL=sqlite:///./data/evosearch.db

# Storage

STORAGE_PATH=./data/uploads

VECTOR_INDEX_PATH=./data/vector_index

# Embeddings

EMBEDDING_MODEL=all-MiniLM-L6-v2

# LLM

GROQ_API_KEY=

LLM_PROVIDER=

LLM_MODEL=

# Uploads

MAX_UPLOAD_MB=25

# Security

SECRET_KEY=change-this-in-production

Local setup

Create your local environment file from the example:

cp backend/.env.example backend/.env

Then update the values that you need.

Important

Never commit:

.env

.env.*

The repository should contain the safe template:

.env.example

but not your real API keys or production secrets.

🐳 Run with Docker

EVOSearch includes Docker support for running the application as a complete stack.

From the project root:

docker compose up --build

After the containers start, the application exposes the frontend and backend according to the ports configured in the Docker Compose file.

The backend provides interactive API documentation through FastAPI.

/docs

Persistent application data

EVOSearch stores important runtime information such as:

SQLite database

Uploaded files

FAISS vector indexes

The Docker setup uses persistent storage so these files are not lost whenever the application container is recreated.

💻 Run Without Docker

1. Start the backend

Create a virtual environment:

cd backend

python -m venv .venv

Activate it.

Windows

.venv\Scripts\activate

Linux / macOS

source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Create your environment file:

cp .env.example .env

Start FastAPI:

uvicorn app.main:app --reload --port 8000

Backend:

http://localhost:8000

(or)

After downloaded the required packages You can run by using:

cd backend

python run_backend.py

API documentation:

http://localhost:8000/docs

2. Start the frontend

Open another terminal:

cd frontend

Install dependencies:

npm ci

Start the development server:

npm run dev

Vite will display the local frontend URL in the terminal.

🔌 Important API Endpoints

Authentication

POST /api/auth/signup

POST /api/auth/login

GET  /api/auth/me

Documents

POST   /api/documents/upload

GET    /api/documents

GET    /api/documents/{id}

GET    /api/documents/{id}/claims

GET    /api/documents/{id}/suggestions

DELETE /api/documents/{id}

Search

POST /api/search

Chat

POST /api/chat

GET  /api/chat/{session_id}/messages

Comparison

POST /api/comparison/documents

Timeline / Knowledge Map

GET /api/timeline/...

Code

POST /api/code/upload

GET  /api/code

POST /api/code/compare

POST /api/code/impact

Health

GET /api/health

🧪 Testing

The backend includes pytest-based tests covering areas such as:

document chunking

code analysis

document comparison

API routers

embedding/import behavior

Run the test suite from the backend environment:

pytest

☁️ Public Deployment Plan

The project can be made publicly accessible by separating the frontend and backend deployment.

A practical first deployment architecture is:

                    Internet

                       │

                       ▼

              ┌─────────────────┐

              │ React Frontend  │

              │ Vercel / Render │

              └────────┬────────┘

                       │ HTTPS API

                       ▼

              ┌─────────────────┐

              │ FastAPI Backend │

              │ Render / Railway│

              └────────┬────────┘

                       │

             ┌─────────┼─────────┐

             ▼         ▼         ▼

          SQLite    Uploads     FAISS

             │         │         │

             └─────────┴─────────┘

               Persistent Disk

Recommended first public deployment

Frontend

Deploy the React/Vite application using:

Vercel

Render Static Site

Backend

Deploy FastAPI using:

Render Web Service

Railway

The backend should listen on the hosting platform's assigned port, for example:

uvicorn app.main:app --host 0.0.0.0 --port $PORT

Persistent storage

Because EVOSearch currently uses local SQLite, uploaded files and local FAISS indexes, the backend needs persistent storage.

Do not rely on an ephemeral container filesystem for production data.

For an initial public deployment, use the hosting provider's persistent disk/volume.

🌐 Frontend ↔ Backend Configuration

When running locally, the frontend can communicate with the local FastAPI backend.

For public deployment, the frontend must point to the deployed backend URL rather than:

localhost:8000

Use the frontend's Vite environment configuration for the public API address.

The backend must also allow the deployed frontend origin through CORS.

Conceptually:

Public Frontend

      │

      │ HTTPS

      ▼

Public FastAPI API

      │

      ▼

Persistent Application Data

🔒 Before Making EVOSearch Public

The current project is suitable for demonstrating and deploying as an application, but a public production deployment should include additional hardening.

Before opening it to everyone:

use a strong production SECRET_KEY

keep API keys out of GitHub

use HTTPS

configure production CORS correctly

keep persistent storage enabled

enforce upload size/type restrictions

add rate limiting

verify authentication and authorization for every protected resource

ensure users cannot access another user's documents

monitor application errors

back up persistent data

avoid executing uploaded source code

use managed database/object/vector services when scaling

🗄️ Current Storage Model

The current architecture intentionally keeps the storage design simple:

                 EVOSearch

                     │

          ┌──────────┼──────────┐

          ▼          ▼          ▼

       SQLite     Filesystem   FAISS

       Metadata     Uploads    Vectors

SQLite

Stores structured application information and metadata.

Filesystem

Stores uploaded documents/files.

FAISS

Stores vector embeddings used for semantic retrieval.

The application connects stored records and vectors through references such as vector_ref.

📊 Evolution Score

EVOSearch includes an Evolution Score represented on a 0–100 scale.

This is a project-defined metric intended to summarize detected change/evolution.

It should not be interpreted as an industry-standard benchmark or universal measure of software/document quality.

🛡️ Security Notes

EVOSearch follows several important safety principles:

Uploaded source code is not executed

Source files are analyzed as data.

Secrets stay outside the repository

Use:

.env

for local secrets and configure production secrets through the hosting platform.

Git ignores runtime data

The repository should not contain:

.env

data/

*.db

*.sqlite

*.sqlite3

*.faiss

node_modules/

Keep:

.env.example

as the safe configuration template.

⚠️ Current Limitations

EVOSearch is intentionally a practical project rather than a complete enterprise platform.

Current limitations include:

Programming-language analysis

Python has stronger AST-based analysis.

Other languages use best-effort extraction and therefore do not provide the same parser depth.

OCR

Scanned documents requiring OCR are not fully supported by the normal text-extraction pipeline.

Impact analysis

Current impact analysis is based on textual/reference search rather than a complete compiler-level call graph.

FAISS scaling

The local FAISS design is convenient for a single application instance but requires architectural changes for large-scale multi-instance deployments.

Database migrations

A production system would benefit from a formal migration system such as Alembic.

Evaluation

A larger labeled benchmark would be needed to formally measure retrieval quality, comparison accuracy and AI-answer quality.

User-level isolation

For a public multi-user system, document ownership and authorization should be thoroughly enforced across every document-related operation.

🔮 Future Improvements

Possible future improvements include:

🌳 Tree-sitter-based multi-language parsing

🗃️ PostgreSQL for production database storage

📦 Object storage such as S3 for uploaded files

🔎 Managed/vector database infrastructure for large-scale retrieval

📝 OCR for scanned documents

🕸️ True code dependency and call-graph analysis

👤 Stronger per-user document isolation

🔑 API keys / OAuth

📊 Larger labeled evaluation datasets

⚡ Streaming AI responses

📈 More advanced evolution analytics

☁️ Multi-instance production architecture

🎯 Why EVOSearch?

Traditional document search answers:

"Where is this text?"

A normal chatbot answers:

"What does this document say?"

A normal code diff answers:

"Which lines changed?"

EVOSearch aims to answer a broader question:

"What changed, what does that change mean, and how has the project evolved?"

That is the central idea behind:

Understand. Compare. Evolve.

🤝 Project Purpose

EVOSearch is designed as a full-stack AI/software-engineering project demonstrating the integration of:

modern frontend development

REST API design

document processing

semantic embeddings

vector search

retrieval-augmented generation

claim-level comparison

source-code analysis

authentication

persistent application storage

Docker-based deployment

It can be used as a foundation for further research and development in document intelligence, software evolution analysis, and AI-assisted project understanding.

📌 Quick Reference

Frontend

React + TypeScript + Vite

Backend

FastAPI + Python

Database

SQLite

Vector Search

FAISS

Embeddings

all-MiniLM-L6-v2

Authentication

JWT + bcrypt

Document Processing

PyMuPDF + python-docx + native parsers

Code Analysis

Python AST + best-effort language parsing

Deployment

Docker Compose

+

Public frontend/backend hosting

+

Persistent storage

⭐ EVOSearch

Understand. Compare. Evolve.