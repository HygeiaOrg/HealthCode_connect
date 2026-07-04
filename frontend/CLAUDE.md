# Claude Code Context

This is a Hackathon POC project. You are acting as the frontend developer.

## Project Structure
- This `frontend/` directory is your workspace.
- The backend is running locally on a separate port.
- **CRUCIAL:** Our shared data schemas are located in `../shared-api-contract.json`. This is the single source of truth for the data models you should expect from the backend.

## Guidelines
- Keep it simple, fast, and visually impressive. 
- You do not need to containerize this frontend; just set up a robust local development environment (e.g., Vite/React or Next.js) that we can run quickly.
- When you initialize the app, remember to mock the API or connect to the local backend endpoints returning the data conforming to the contract.
