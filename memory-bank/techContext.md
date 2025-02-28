# Technical Context

## Technology Stack
- **Web Framework**: Flask
- **Database**: MariaDB
- **ORM**: SQLAlchemy
- **Background Jobs**: Custom job processor
- **Frontend**: HTML/CSS/JavaScript
- **Charts**: Chart.js
- **Authentication**: Flask-Login
- **API Client**: Requests

## Development Environment
- **Primary IDE**: VSCode
- **Version Control**: Git
- **Package Management**: pip
- **Virtual Environment**: venv
- **Testing Framework**: pytest
- **Linting**: flake8
- **Formatting**: black

## Key Dependencies
- Flask
- SQLAlchemy
- Requests
- Flask-Login
- python-dotenv
- marshmallow
- pytest
- gunicorn

## Deployment Environment
- **Host**: Raspberry Pi 4
- **OS**: Raspberry Pi OS
- **Web Server**: Gunicorn + Nginx
- **Database**: MariaDB
- **Process Management**: systemd
- **Logging**: journalctl

## Configuration Management
- Environment variables via .env
- Centralized configuration module
- Version-controlled secrets
- Separate dev/prod configurations
- Automated environment setup

## Development Workflow
1. Feature branch development
2. Automated testing
3. Code review process
4. Staging deployment
5. Production rollout
