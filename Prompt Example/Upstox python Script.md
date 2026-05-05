You are a senior Python architect and financial systems engineer.

Your task is to design and implement a production-grade Python application for analyzing investment data from the Upstox API.

========================
🎯 GOAL
========================
Build a modular, secure, and extensible Python application that:
- Connects to the Upstox API
- Fetches portfolio, holdings, and transaction data
- Performs investment analysis
- Outputs structured insights and reports

========================
🔐 SECURITY REQUIREMENTS (CRITICAL)
========================
- NEVER hardcode API keys in source code
- Store API keys securely using:
  - .env file (with python-dotenv) OR
  - OS environment variables
- Add .env to .gitignore
- Provide a sample .env.example file
- Implement a config loader module
- Validate that API key exists before execution
- Do NOT print or log sensitive data

========================
🏗️ ARCHITECTURE (MANDATORY)
========================
Use clean, scalable architecture:

/app
  /core
    config.py
    logger.py
  /api
    upstox_client.py
  /services
    portfolio_service.py
    analysis_service.py
  /models
    portfolio.py
  /utils
    helpers.py
  main.py

========================
⚙️ FEATURES (PHASE 1)
========================
1. Authentication with Upstox API
2. Fetch:
   - Holdings
   - Positions
   - Transactions
3. Data normalization layer
4. Basic analysis:
   - Total investment
   - Current value
   - Profit/Loss
   - Percentage return

========================
📊 ADVANCED ANALYSIS (PHASE 2)
========================
Design the system so these can be added later:
- Risk analysis
- Sector allocation
- Diversification score
- Historical performance
- Moving averages
- Alerts (profit/loss thresholds)

========================
🧠 DESIGN PRINCIPLES
========================
- Follow SOLID principles
- Use dependency injection where possible
- Separate API logic from business logic
- Write reusable services
- Make it easy to plug in new brokers later (not only Upstox)

========================
📦 OUTPUT FORMAT
========================
Provide:
1. Full project structure
2. All Python files with code
3. requirements.txt
4. .env.example
5. .gitignore (must exclude secrets)
6. README.md with:
   - Setup instructions
   - How to run
   - How to extend

========================
🧪 TESTING
========================
- Add basic unit test examples
- Mock API responses

========================
🧾 OUTPUT STYLE
========================
- Clean, well-commented code
- Professional naming conventions
- No unnecessary verbosity
- Use type hints

========================
🚫 CONSTRAINTS
========================
- Do NOT use insecure storage
- Do NOT expose API keys
- Do NOT mix UI and backend logic

========================
🔄 EXTENSIBILITY (VERY IMPORTANT)
========================
Design so future features can be added easily:
- Add new APIs
- Add ML-based prediction
- Add dashboard (e.g., Vue.js frontend)
- Add database storage

========================
🧠 BONUS (IF POSSIBLE)
========================
- Add CLI interface (argparse or typer)
- Add logging system
- Add caching layer

========================

Before writing code:
1. Explain the architecture briefly
2. Then generate the full implementation