# CLAUDE.md (Developer Guidelines)

This file contains build, run, deploy instructions, codebase structure, and coding standards for the **AI-Powered Email Threat Detection, GeoLocation & Forensic Intelligence Platform**.

---

## 🚀 Build & Run Commands

### 1. Frontend (React / Vite)
Located in `/frontend`.

*   **Install dependencies**:
    ```bash
    cd frontend && npm install
    ```
*   **Run local development server**:
    ```bash
    cd frontend && npm run dev
    ```
*   **Build production bundle**:
    ```bash
    cd frontend && npm run build
    ```
*   **Preview production build locally**:
    ```bash
    cd frontend && npm run preview
    ```

### 2. Forensics API Backend (Python / FastAPI)
Located in `/Forensics/SIH-main`.

*   **Install dependencies**:
    ```bash
    cd Forensics/SIH-main && pip install -r requirements.txt
    ```
*   **Run local FastAPI server**:
    ```bash
    cd Forensics/SIH-main && uvicorn main:app --reload
    ```
    *API documentation is available locally at `http://127.0.0.1:8000/docs` after running.*

---

## 📂 Project Structure

```
├── .github/workflows/    # CI/CD Workflows
│   └── deploy-frontend.yml # Frontend deployment to GitHub Pages (triggers on `frontend` branch)
├── docs/                 # Platform Design & Specifications
│   ├── aiml-README.md     # NLP content analysis, fraud scoring & identity correlation specs
│   ├── forensics-README.md# Header/protocol analysis, tracing, & domain intel specs
│   ├── software-dev-README.md # Gateway API, authentication, case & alert DB schemas
│   └── design.md          # UX workflows, role mapping & information architecture
├── frontend/             # Frontend Dashboard Single-Page App (React / Vite)
│   ├── src/
│   │   ├── main.jsx       # Core React component views (Command Center, Inbox, Threat Map, Drawer)
│   │   └── styles.css     # Styling for Dashboard and components
│   ├── package.json       # Frontend dependencies and npm scripts
│   └── vite.config.js     # Configured with base relative path './' for deployments
├── Forensics/            # Backend Services
│   └── SIH-main/          # Cyber Forensics API service (FastAPI)
│       ├── main.py        # Single-file FastAPI application containing endpoints
│       ├── requirements.txt # Python package dependencies
│       └── vercel.json    # Vercel deployment configuration
├── .gitignore            # Excludes node_modules, .DS_Store, build artifacts, etc.
└── README.md             # Shared Data Contracts & High-Level System Architecture
```

---

## 🛠️ Code Style & Guidelines

### Frontend (React & CSS)
*   **Component Structure**: Keep components modular or build helper rendering sections within main layouts. Follow the JSX pattern.
*   **Routing**: Use local state management (like `activeNav` tabs) to toggle sub-views (e.g. Command Center, Threat Inbox).
*   **Styling**: Add utility and component classes in `styles.css`. Maintain color-coded bands for threat levels (`critical`, `high`, `medium`, `low`).
*   **Vite base path**: Ensure `base: './'` is always set in `vite.config.js` to preserve path resolving on GitHub Pages and local builds.

### Backend (Python & FastAPI)
*   **Type Safety**: Define Request/Response payloads using Pydantic models (subclassing `BaseModel`).
*   **Route Setup**: Organize routing using FastAPI tags for clear OpenAPI categorization.
*   **Error Handling**: Throw `HTTPException(status_code, detail=...)` for validation, resource unavailability, or upstream communication errors.
*   **CORS**: Keep CORS middleware configuration in `main.py` properly permissive during development/integration.

---

## ☁️ Deployment Configuration
*   **Frontend**: Automatically builds and deploys to GitHub Pages when commits are pushed to the `frontend` branch.
*   **Backend (Forensics API)**: Deploys using Vercel using the configuration found in `vercel.json`.
