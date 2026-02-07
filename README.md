# AegisAI

<div align="center">

![AegisAI](https://img.shields.io/badge/AegisAI-1.1.1-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal)
![MongoDB](https://img.shields.io/badge/MongoDB-4.4+-success)

**Comprehensive AI/ML Platform for Language Model Training, Data Management, and Security**

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Technologies Used](#technologies-used)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Modules](#modules)
- [Security](#security)

---

## Overview

**AegisAI** is a comprehensive artificial intelligence platform designed for language model training, data management, and security. Built with FastAPI and MongoDB, it provides a complete ecosystem for:

- Training and fine-tuning language models
- Data scraping and dataset management
- Multi-language text processing (English, Turkish)
- Security features including bot detection and content moderation
- Comprehensive reporting and analytics

The platform follows a modular architecture with service-oriented design patterns, making it highly extensible and maintainable.

---

## Technologies Used

### Backend Framework

| Technology | Version | Purpose |
|------------|---------|---------|
| **FastAPI** | 0.100+ | Modern, fast web framework for building APIs |
| **Uvicorn** | Latest | ASGI server for running FastAPI applications |
| **APScheduler** | Latest | Background task scheduling |

### Database

| Technology | Version | Purpose |
|------------|---------|---------|
| **MongoDB** | 4.4+ | NoSQL database for data storage |
| **PyMongo** | Latest | MongoDB driver for Python |

### Authentication & Security

| Technology | Purpose |
|------------|---------|
| **python-jose[cryptography]** | JWT token handling |
| **passlib[bcrypt]** | Password hashing |
| **python-multipart** | Form data handling |

### AI/ML

| Technology | Purpose |
|------------|---------|
| **Transformers** | HuggingFace transformer models |
| **PyTorch** | Deep learning framework |
| **Torch** | Tensor operations |

### Data Processing

| Technology | Purpose |
|------------|---------|
| **Pandas** | Data manipulation and analysis |
| **OpenPyXL** | Excel file handling |
| **ReportLab** | PDF report generation |

### Web Scraping

| Technology | Purpose |
|------------|---------|
| **Requests** | HTTP library for web requests |
| **BeautifulSoup4** | HTML parsing |

### Utilities

| Technology | Purpose |
|------------|---------|
| **Pydantic** | Data validation using Python type annotations |
| **python-dotenv** | Environment variable management |

---

## Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| 🤖 **Model Training** | Train language models from scratch with custom corpora |
| 🔧 **Fine-tuning** | Fine-tune existing models on custom datasets |
| 📊 **Dataset Builder** | Create and manage training datasets |
| 🌐 **Data Scraper** | Scrape Reddit data for training purposes |
| 📚 **Corpus Management** | Manage text corpora efficiently |
| 🌍 **Multi-language** | Support for English and Turkish languages |
| 🛡️ **Security** | Bot detection, PII detection, doxxing detection |
| 🚫 **Profanity Filter** | Advanced profanity detection and masking |
| 📝 **Template System** | Dynamic template management |
| 📈 **Reports** | Training cost reports and analytics |
| 🔐 **Authentication** | JWT-based authentication system |
| 📜 **Audit Logging** | Comprehensive audit trail |
| ⚡ **Rate Limiting** | API rate limiting protection |

### Advanced Features

- **Scenario Intelligence**: AI-powered training scenario analysis
- **Cost Calculator**: Training cost estimation and tracking
- **PDF Reports**: Generate professional PDF reports
- **Excel Reports**: Export training data to Excel
- **Obfuscation Detection**: Detect and resolve text obfuscation
- **Device Management**: Track user devices
- **Workspace Management**: Organize workspaces for different projects

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         FastAPI App                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Controllers│  │  Middlewares │  │  Exception   │      │
│  │              │  │              │  │   Handlers   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │              │
│  ┌──────▼─────────────────▼─────────────────▼───────┐     │
│  │                   Services Layer                  │     │
│  └──────┬─────────────────┬─────────────────┬───────┘     │
│         │                 │                 │              │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐       │
│  │   Business  │  │   Security  │  │   Utility   │       │
│  │   Logic     │  │   Modules   │  │   Services  │       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
│         │                 │                 │              │
│  ┌──────▼─────────────────▼─────────────────▼───────┐     │
│  │                    MongoDB                       │     │
│  └───────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

Before installing AegisAI, ensure you have the following:

- **Python**: 3.8 or higher
- **MongoDB**: 4.4 or higher
- **pip**: Python package manager
- **Git**: For the repository
---

## Usage

### Starting the Application

```bash
# Development mode with auto-reload
python main.py

# Or using uvicorn directly
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

The application will be available at `http://127.0.0.1:8000`

---

## Project Structure

```
AegisAI/
├── app.py                          # FastAPI application entry point
├── main.py                         # Application launcher
├── config.json                     # Application configuration
├── config_loader.py                # Configuration loader utility
├── .env                            # Environment variables
├── .gitignore                      # Git ignore rules
│
├── auth/                           # Authentication module
│   └── authcontroller.py
│
├── auditmanager/                   # Audit logging module
│   ├── auditlog_controller.py
│   ├── auditlog_service.py
│   ├── auditlog.py
│   ├── auditlogserviceimpl.py
│   ├── create/
│   ├── response/
│   └── upsert/
│
├── corpusmanagement/               # Corpus management module
│   ├── corpus_controller.py
│   └── corpusmanager.py
│
├── corpora/                        # Training corpora files
│   ├── wiki_en_clean.txt
│   ├── wiki_tr_clean.txt
│   └── *.meta.json
│
├── data_scraper/                   # Data scraping module
│   ├── scrapper_controller.py
│   ├── scrapper_service.py
│   ├── scrapper_serviceimpl.py
│   ├── scrapper_cache.py
│   ├── scrapper_dataset_integrator.py
│   ├── scrapper_logging.py
│   └── sites/
│       └── reddit_scrapper.py
│
├── dataset_builder/                # Dataset building module
│   ├── dataset_builder_controller.py
│   ├── dataset_builder_service.py
│   ├── dataset_builder_serviceimpl.py
│   ├── dataset_builder.py
│   ├── datasettype.py
│   ├── entrytype.py
│   ├── create/
│   ├── response/
│   └── upsert/
│
├── device/                         # Device management module
│   └── devicecontroller.py
│
├── error/                          # Error handling module
│   ├── errorcodes.py
│   ├── errortypes.py
│   └── expectionhandler.py
│
├── huggingface/                    # HuggingFace integration module
│   ├── huggingface_controller.py
│   └── huggingfacemanager.py
│
├── logs/                           # Application logs
│   ├── scrape_logs.jsonl
│   └── predictionlogmanager.py
│
├── multilangsetup/                 # Multi-language setup module
│   ├── multilang_controller.py
│   ├── multilang_service.py
│   ├── multilang_serviceimpl.py
│   ├── multilang_processor.py
│   ├── multilang_step.py
│   ├── constants/
│   │   └── english.py
│   ├── normalizers/
│   │   ├── english_normalizer.py
│   │   └── turkish_normalizer.py
│   ├── obsfucationresolver/
│   │   ├── obsfucation_helper.py
│   │   ├── obsfucation_resolver.py
│   │   └── obsfucation_util.py
│   └── schemas/
│       ├── multilang_request.py
│       └── multilang_response.py
│
├── obsf/                           # Obfuscation configuration
│   ├── obfuscation_config_loader.py
│   ├── obfuscation_config.json
│   └── languages/
│       ├── en.json
│       └── tr.json
│
├── permcontrol/                    # Permissions control module
│   └── permissionscontrol.py
│
├── profanity/                      # Profanity detection module
│   ├── profanitycontroller.py
│   ├── profanityservice.py
│   ├── profanityserviceimpl.py
│   ├── messagelevelmetadata.py
│   ├── maskingrules/
│   │   ├── maskingruleautomation.py
│   │   └── maskingruleutil.py
│   └── schemas/
│       ├── profanityrequest.py
│       └── profanityresponse.py
│
├── ratelimit/                      # Rate limiting module
│   ├── ratelimit.py
│   └── ratelimitutility.py
│
├── reports/                        # Generated reports
│   ├── training_cost_report_*.pdf
│   └── test_reports.pdf
│
├── revokedtokenservice/            # Revoked token service
│   ├── revoked_token_service.py
│   └── check_clean_tokens.py
│
├── security/                       # Security module
│   ├── bot_detection/
│   │   ├── botdetectioncontroller.py
│   │   ├── botdetectionservice.py
│   │   ├── botdetectionserviceimpl.py
│   │   ├── bot_detection.py
│   │   ├── bot_engine.py
│   │   ├── behaviorscore.py
│   │   ├── bot_detection_logger.py
│   │   ├── botverdictresolver.py
│   │   ├── behavior_features.py
│   │   ├── models/
│   │   │   ├── model.py
│   │   │   ├── model_config.py
│   │   │   └── model_utils.py
│   │   └── schemas/
│   │       ├── bot_detection_request.py
│   │       └── bot_detection_response.py
│   └── breach/
│       ├── infraction/
│       │   ├── infractioncontroller.py
│       │   ├── infractionservice.py
│       │   ├── infractionserviceimpl.py
│       │   └── infraction_result.py
│       ├── actions/
│       │   ├── actiondecision.py
│       │   └── actionpolicy.py
│       ├── context_detector.py
│       ├── doxxing_detector.py
│       ├── doxxing_settings.py
│       ├── pii_detector.py
│       ├── socialmediaformats.py
│       └── langs/
│           ├── en.py
│           └── tr.py
│
├── template/                       # Template management module
│   ├── templatecontroller.py
│   ├── templateservice.py
│   ├── templateserviceimpl.py
│   ├── template.py
│   ├── create/
│   ├── response/
│   ├── upsert/
│   └── utils/
│       ├── extract_placeholders.py
│       └── templategenerator.py
│
├── trainer/                        # Training module
│   ├── service/
│   │   ├── trainer_service.py
│   │   └── trainer_service_impl.py
│   ├── modelregistry.py
│   ├── trainer_utils.py
│   ├── base_trainer/
│   │   ├── base_trainer_controller.py
│   │   └── base_trainer.py
│   ├── finetune_trainer/
│   │   ├── finetune_trainer_controller.py
│   │   ├── finetune_trainer.py
│   │   └── schema/
│   │       └── fine_tune_request.py
│   └── reports/
│       ├── reports_controller.py
│       ├── reports_service.py
│       ├── reports_service_impl.py
│       ├── training_report.py
│       ├── training_tracker.py
│       ├── trainingvalidation.py
│       ├── excel_report.py
│       ├── report_config.py
│       ├── report_config.json
│       ├── create/
│       ├── response/
│       ├── core/
│       │   ├── training_scenario.py
│       │   └── scenario_cost_calculator.py
│       ├── intelligence/
│       │   ├── scenario_intelligence.py
│       │   └── scenario_intelligence_utils.py
│       └── templates/
│           ├── default_pdf.py
│           └── core/
│               ├── report_base_template.py
│               └── pdftemplate.py
│
├── user/                           # User management module
│   ├── usercontroller.py
│   ├── userservice.py
│   ├── userserviceimpl.py
│   ├── user.py
│   ├── role.py
│   ├── language.py
│   ├── device.py
│   ├── rule.py
│   ├── ruletype.py
│   ├── validationmixin.py
│   ├── censormode.py
│   ├── censorsettings.py
│   ├── censorvisibility.py
│   ├── advisory_policy.py
│   ├── create/
│   ├── response/
│   ├── upsert/
│   ├── devicemanager/
│   │   └── devicemanager.py
│   ├── utility/
│   │   └── failedloginattempt_service.py
│   └── verifymanagement/
│       └── verifymanager.py
│
├── utility/                        # Utility functions
│   └── client_ip_middleware.py
│
└── workspace/                      # Workspace management module
    └── workspacecontroller.py
```

---

## Modules

### Authentication Module ([`auth/`](auth/))

Handles user authentication and authorization using JWT tokens.

**Features:**
- User registration and login
- JWT token generation and validation
- Token revocation support
- Password hashing with bcrypt

### Data Scraper Module ([`data_scraper/`](data_scraper/))

Provides web scraping capabilities for collecting training data.

**Features:**
- Reddit data scraping
- Configurable user agents
- Request caching
- Logging and tracking

### Dataset Builder Module ([`dataset_builder/`](dataset_builder/))

Create and manage training datasets from various sources.

**Features:**
- Dataset creation from scraped data
- Multiple entry types support
- Dataset validation
- CRUD operations

### Trainer Module ([`trainer/`](trainer/))

Core module for training and fine-tuning language models.

**Features:**
- Base model training
- Fine-tuning existing models
- Model registry management
- Training cost calculation
- PDF and Excel report generation

### Security Module ([`security/`](security/))

Comprehensive security features for protecting the platform.

**Features:**
- **Bot Detection**: ML-based bot detection using behavior analysis
- **PII Detection**: Detect personally identifiable information
- **Doxxing Detection**: Detect doxxing attempts
- **Infraction Detection**: Policy violation detection

### Profanity Module ([`profanity/`](profanity/))

Advanced profanity detection and content moderation.

**Features:**
- Multi-language profanity detection
- Configurable masking rules
- Message-level metadata
- Customizable sensitivity

### Multi-language Module ([`multilangsetup/`](multilangsetup/))

Support for multiple languages with text normalization.

**Features:**
- English and Turkish support
- Text normalization
- Obfuscation detection and resolution
- Language-specific processing

### Template Module ([`template/`](template/))

Dynamic template management system.

**Features:**
- Template creation and management
- Placeholder extraction
- Template generation
- Variable substitution

### Audit Manager Module ([`auditmanager/`](auditmanager/))

Comprehensive audit logging for compliance and security.

**Features:**
- Action logging
- User activity tracking
- Audit trail generation
- Query and filtering

### HuggingFace Module ([`huggingface/`](huggingface/))

Integration with HuggingFace model hub.

**Features:**
- Model download
- Model upload
- Model metadata management

---

## Security

### Authentication

- JWT-based authentication with configurable expiration
- Password hashing using bcrypt
- Token revocation support
- Failed login attempt tracking

### Rate Limiting

- Configurable rate limiting middleware
- Default: 5 requests per 10 seconds per IP
- Customizable per endpoint

### Bot Detection

- Behavior-based bot detection
- Machine learning models
- Event tracking and analysis
- Configurable thresholds

### Content Security

- PII detection and masking
- Doxxing detection
- Profanity filtering
- Social media format detection

### Data Protection

- MongoDB authentication
- Environment variable support for secrets
- Audit logging for sensitive operations

---


## Authors

- **Tuna Rasim Ocak** - *Project Owner / Lead Developer*

---