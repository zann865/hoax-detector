# HoaxCheck - Original Structure, Render Ready

This version retains the original folders:

- `backend/main.py`: FastAPI API and web-page route.
- `backend/requirements.txt`: Python dependencies.
- `frontend/index.html`: original interface.
- `render.yaml`: one-service Render Blueprint configuration.

## Deploy

1. Extract this ZIP.
2. Upload the **contents** of this folder to the root of a GitHub repository.
3. In Render, choose **New > Blueprint** and select the GitHub repository.
4. Enter a new Groq key when Render asks for `GROQ_API_KEY`.
5. Deploy, then open the generated `onrender.com` URL.

Do not commit an `.env` file or any Groq API key to GitHub.
