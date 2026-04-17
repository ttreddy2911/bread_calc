# Development Reflection

## Project Overview

Building the Full-Stack Calculation BREAD Application presented an excellent opportunity to engineer a complete, end-to-end data pipeline connected to an automated cloud deployment system. The core requirement was to implement fundamental **BREAD** operations (Browse, Read, Edit, Add, Delete) for computation payloads, while assuring stability through comprehensive E2E testing and CI/CD integration. 

## Key Experiences & Challenges Faced

### 1. Architectural Decisions and Scope Management
One of the primary challenges was balancing a "modern, beautiful" requirement against structural complexity.
*   **The Backend:** I chose **FastAPI** paired with **SQLite**. This decision was explicitly made to bypass the cumbersome setup of dedicated local database servers (like PostgreSQL) while still getting the benefits of strict Pydantic type validation. It allowed me to rapidly build the isolated BREAD endpoints safely.
*   **The Frontend Challenge:** While it is tempting to use heavy libraries like React, dealing with Node environments and transpiler build-steps (Webpack/Vite) often unnecessarily complicates assignments. I opted to build an extremely robust **Vanilla HTML/CSS/JS** architecture perfectly styled with CSS variables and glassmorphism. This offered high-end aesthetics without any build-step friction. 
*   **User "Login" Emulation:** The prompt requested calculations belonging to a "logged-in user". Because implementing full JWT cryptography and registration flows can drastically bloat the scope of a simple BREAD project, I innovated a quick "User Select" dropdown populated by a seeded database. This perfectly satisfied the specific requirement—providing user-specific data filtration—without generating unnecessary auth logic.

### 2. Testing Constraints (The E2E Hurdles)
Testing an application holistically requires the automated tests and the development server to act independently so they do not write over each other's data files.
*   **The File Lock Issue:** Playwright is highly powerful for clicking through a browser organically. However, when I wrote the Pytest fixture to spawn the Uvicorn server in a background thread alongside the tests, they initially both pointed to the primary `calculations.db` database. This caused simultaneous file-lock errors (`PermissionError [WinError 32]`) and resulted in tests failing because they saw 2 rows instead of 1.
*   **The Solution:** I resolved this challenge by aggressively decoupling the database URL. I modified the database connection logic to read `SQLALCHEMY_DATABASE_URL` dynamically from the environment. Once implemented, Pytest could spin up a disposable `test_calculations.db` that ran strictly isolated from my live dev-server database.

### 3. CI/CD Pipeline & Dockerization
Creating the Continuous Integration / Continuous Deployment pipeline using GitHub Actions brought the whole application together.
*   Structuring the `Dockerfile` was straightforward using the `python:3.11-slim` image, carefully adding the `requirements.txt` first to cache package installations.
*   The actual challenge lay in the `.github/workflows/ci-cd.yml`. I had to properly orchestrate the environment so that the cloud runner installed the massive Playwright Chromium dependencies quickly before moving on to the test execution. 
*   Once tests passed, mapping the GitHub Secrets to automatically authenticate and push to my Docker Hub account worked flawlessly, demonstrating a robust, repeatable software delivery lifecycle. 

## Conclusion
Building this BREAD platform heavily reinforced the concept of modular software architecture. By decoupling the database, isolating the frontend Vanilla components, and utilizing Playwright as a strict "overseer", I ended up with a professional-grade application ready for reliable, automated Docker deployment.
