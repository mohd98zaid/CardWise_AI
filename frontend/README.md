# Frontend

React/TypeScript alpha workspace for the CardWise AI synthetic calculation flow.

## Run locally

Start the backend first, then run:

```bash
npm install
npm run dev
```

The Vite development server uses `http://localhost:8000` as the API by default. Set
`VITE_API_BASE_URL` when the API is hosted elsewhere.

## Check

```bash
npm run build
```

Frontend validation is for usability; the backend remains authoritative for rules and calculations.
