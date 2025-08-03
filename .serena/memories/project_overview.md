# MMA Savant Project Overview

MMA Savant is a comprehensive Mixed Martial Arts (MMA) data collection and analysis platform that consists of two main components:

## Main Components

1. **Data Collectors (Crawlers)**: Automated web scrapers for collecting MMA data from external sites
2. **Backend API (src)**: Web service API and backend logic for serving the collected data

## Tech Stack

- **Backend**: Python 3.12+ with FastAPI
- **Database**: PostgreSQL 13 with asyncpg/SQLAlchemy
- **Caching**: Redis 8.0-alpine  
- **Workflow Orchestration**: Prefect for scheduling data collection
- **Web Scraping**: Playwright and httpx for data collection
- **Chat Interface**: Chainlit for conversational AI interface
- **LLM Integration**: OpenAI/Anthropic with LangChain
- **Containerization**: Docker with docker-compose

## Architecture

The project follows a clean architecture pattern:
- **Repository Pattern**: Data access layer with proper separation
- **Service Layer**: Business logic between API and repositories  
- **Domain-Driven Design**: Organized by domains (fighter, event, match, user, conversation)
- **MCP Integration**: Tools for querying MMA data via conversational interface

## Project Purpose

MMA Savant provides:
- Comprehensive fighter profiles and statistics
- Event information and match details
- Fighter rankings and weight class analysis
- Advanced analytics and comparisons
- Conversational AI interface for data queries
- Performance metrics and insights