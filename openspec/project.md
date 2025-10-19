# Project Context

## Purpose
This project provides a web-based user interface for trading and portfolio management through Interactive Brokers (IBKR). It wraps the IBKR Client Portal Gateway REST API with a Flask web application, enabling users to:
- View account summaries and portfolio positions
- Look up securities and view contract details with price history
- Place, view, and cancel orders
- Create and manage watchlists
- Run market scans to discover trading opportunities

The goal is to provide a simple, accessible web interface for IBKR trading operations without needing to use the native client applications.

## Tech Stack
- **Backend Framework**: Python 3.11 with Flask
- **IBKR Integration**: Interactive Brokers Client Portal Gateway (Java-based)
- **HTTP Client**: Python requests library
- **Containerization**: Docker & Docker Compose
- **Base Image**: Debian Bookworm Slim
- **Java Runtime**: OpenJDK 17 JRE
- **Template Engine**: Jinja2 (Flask default)
- **SSL/TLS**: Self-signed certificates (vertx.jks)

## Project Conventions

### Code Style
- **Python**: Follow PEP 8 conventions
- **Naming**: Use snake_case for functions and variables
- **Flask Routes**: Use RESTful patterns where appropriate
- **Templates**: Store in `webapp/templates/` directory
- **Configuration**: Environment variables for sensitive data (e.g., `IBKR_ACCOUNT_ID`)
- **Error Handling**: Use try-except blocks for external API calls

### Architecture Patterns
- **Deployment**: Multi-container Docker setup with single service
- **API Communication**: Flask app acts as a proxy to IBKR Gateway API
- **Port Allocation**: 
  - 5055: IBKR Client Portal Gateway (HTTPS)
  - 5056: Flask web application (HTTP)
- **SSL**: Gateway uses SSL, Flask app communicates over SSL to gateway
- **Session Management**: Authentication handled by IBKR Gateway
- **File Structure**:
  ```
  /app/
    gateway/          # IBKR Client Portal Gateway
    webapp/           # Flask application
      app.py          # Main application logic
      templates/      # Jinja2 HTML templates
      requirements.txt
    scripts/          # Example API scripts
    conf.yaml         # Gateway configuration
    start.sh          # Startup script
  ```

### Testing Strategy
- Manual testing through web interface
- Test against IBKR paper trading accounts before live trading
- Verify SSL certificate warnings are handled appropriately
- Test order placement with small quantities on test accounts

### Git Workflow
- Repository follows standard GitHub workflow
- Main branch for stable releases
- Feature branches for new capabilities
- Descriptive commit messages

## Domain Context

### IBKR Trading Concepts
- **Contract ID (conid)**: Unique identifier for financial instruments in IBKR system
- **Account ID**: IBKR account identifier (format: U1234567)
- **Order Types**: Supports limit orders (LMT) with time-in-force (TIF) specifications
- **Watchlists**: User-created lists of contracts for monitoring
- **Scanner**: IBKR market scanner for discovering securities based on criteria

### API Endpoints Used
- Portfolio: `/v1/api/portfolio/`
- Market Data: `/v1/api/iserver/marketdata/`
- Orders: `/v1/api/iserver/account/orders`
- Security Definitions: `/v1/api/iserver/secdef/`
- Watchlists: `/v1/api/iserver/watchlists`
- Scanner: `/v1/api/iserver/scanner/`

### Authentication Flow
Users must authenticate through the IBKR Gateway web interface at `https://localhost:5055` before using the Flask application. The Gateway maintains the session.

## Important Constraints

### Technical Constraints
- **SSL Verification Disabled**: Currently using `verify=False` for requests due to self-signed certificates
- **Single Account**: Application designed for single account access (configured via environment variable)
- **Gateway Dependency**: Flask app requires IBKR Gateway to be running and authenticated
- **Session Timeout**: IBKR sessions timeout after period of inactivity
- **Rate Limiting**: Subject to IBKR API rate limits
- **Java Dependency**: Requires Java runtime for Gateway operation

### Regulatory Constraints
- Subject to IBKR terms of service and API usage policies
- Trading operations must comply with securities regulations
- Users responsible for their own trading decisions and compliance

### Business Constraints
- Requires active IBKR brokerage account
- May require market data subscriptions for certain securities
- Paper trading account recommended for testing

## External Dependencies

### Interactive Brokers Client Portal Gateway
- **Source**: https://download2.interactivebrokers.com/portal/clientportal.gw.zip
- **Purpose**: REST API gateway for IBKR trading operations
- **Configuration**: Uses `conf.yaml` for settings
- **Authentication**: Web-based login at port 5055

### IBKR API
- **Host**: https://api.ibkr.com (configured as proxy in Gateway)
- **Version**: v1
- **Documentation**: IBKR Client Portal Web API documentation
- **Environment**: Production API (can be configured for paper trading)

### Python Dependencies
- **flask**: Web framework for application
- **requests**: HTTP client for API communication

### System Dependencies
- **Docker Desktop**: Required for containerization
- **OpenJDK 17**: Java runtime for Gateway
- **Python 3.11**: Runtime for Flask application
