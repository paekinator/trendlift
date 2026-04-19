# TrendLift

TrendLift is a creator intelligence tool for small YouTube creators.

It helps users:
- validate whether a topic is crowded or accessible
- find breakout-friendly niches
- understand title patterns in trending content

## Project Structure

- `backend/` FastAPI backend
- `frontend/` React + Vite frontend
- `data/processed/` cleaned and engineered datasets

## Local Development

### Backend
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload