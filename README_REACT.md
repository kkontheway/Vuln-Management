# React Frontend Setup

This project has been refactored to use React for the frontend. The React application is located in the `frontend/` directory.

## Development Setup

### Prerequisites
- Node.js 18+ (or Node.js 16 with legacy peer deps)
- npm or yarn

### Install Dependencies

```bash
cd frontend
npm install
```

### Development Mode

Run the React development server (runs on port 3000):

```bash
cd frontend
npm run dev
```

The React app will proxy API requests to the FastAPI backend running on `http://localhost:5001`.

### Production Build

Build the React app for production:

```bash
cd frontend
npm run build
```

This will create a `dist/` directory with the production build.

### Running with FastAPI Backend

1. Build the React app:
   ```bash
   cd frontend
   npm run build
   ```

2. Run the FastAPI backend:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 5001 --reload
   # or python app.py
   ```

3. Access the application at `http://localhost:5001`

The FastAPI backend is configured to serve the React app from `frontend/dist/` for all non-API routes.

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable React components
│   │   ├── Sidebar/
│   │   ├── Header/
│   │   ├── Charts/
│   │   ├── Table/
│   │   ├── FilterPanel/
│   │   ├── ChatBox/
│   │   └── Modals/
│   ├── pages/           # Page components
│   │   ├── Dashboard.jsx
│   │   ├── Vulnerabilities.jsx
│   │   └── ChatConfig.jsx
│   ├── services/        # API service layer
│   │   └── api.js
│   ├── utils/           # Utility functions
│   │   ├── formatters.js
│   │   └── constants.js
│   ├── styles/          # Global styles
│   │   └── globals.css
│   ├── App.jsx          # Main app component
│   └── main.jsx         # Entry point
├── public/              # Static assets
├── package.json
└── vite.config.js       # Vite configuration
```

## Features

- **React Router**: Client-side routing
- **Recharts**: Chart library for data visualization
- **Axios**: HTTP client for API calls
- **Component-based Architecture**: Modular and maintainable code structure
- **Base44 Design Style**: Maintains the original design aesthetic

## Migration Notes

The frontend has been fully migrated to React. All functionality from the previous HTML/CSS/JavaScript implementation has been preserved and improved with better code organization and maintainability.
