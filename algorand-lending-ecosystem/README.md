# Algorand Lending Ecosystem

A comprehensive lending platform built on Algorand blockchain technology, providing secure, transparent, and efficient loan management capabilities.

## Architecture Overview

The lending ecosystem is organized into four main layers:

### 1. Business Logic Engines
Core business logic for loan processing and decision making:
- **Interest Rate Determiner**: Calculates appropriate interest rates based on risk assessment and market conditions
- **Loan Approval Decision Engine**: Makes loan approval decisions using comprehensive risk analysis
- **Risk Assessment Calculator**: Provides detailed risk scoring and assessment

### 2. Data Persistence Layer
Database management and data storage:
- **Database Schema Manager**: Manages database schema, migrations, and versioning
- **Loan Record Repository**: Handles loan data persistence and retrieval
- **Audit Event Storage**: Stores audit trails for compliance and tracking
- **Risk Assessment Archive**: Archives risk assessment data for historical analysis

### 3. API Gateway Services
REST API services for external integration:
- **Loan Application API**: Handles loan application submissions and management
- **Risk Assessment API**: Provides risk assessment services via REST endpoints
- **Audit Trail API**: Offers audit trail access and compliance reporting

### 4. Shared Libraries
Common utilities and models used across the ecosystem:
- **Common Models**: Shared data models and schemas
- **Utility Functions**: Common validation, calculation, and formatting utilities
- **Configuration Management**: Centralized configuration management

## Getting Started

### Prerequisites
- Python 3.8+
- SQLite (for development) or PostgreSQL (for production)
- Algorand SDK

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m algorand_lending_ecosystem.data_persistence_layer.database_schema_manager.migration_runner

# Run tests
pytest tests/
```

### Configuration
Configure the system using environment variables or configuration files in the `config/` directory.

## Usage

### Basic Loan Processing Flow
1. Submit loan application via Loan Application API
2. System performs risk assessment using Risk Assessment Calculator
3. Loan Approval Decision Engine makes approval decision
4. If approved, Interest Rate Determiner calculates rates
5. All actions are logged in Audit Trail

### API Endpoints
- `POST /api/loans/apply` - Submit loan application
- `GET /api/loans/{loan_id}` - Get loan status
- `POST /api/risk/assess` - Request risk assessment
- `GET /api/audit/events` - Query audit events

## Contributing
Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the LICENSE file for details.