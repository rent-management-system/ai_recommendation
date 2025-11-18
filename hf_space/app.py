import uvicorn

if __name__ == "__main__":
    # Hugging Face Spaces expects the app to listen on 0.0.0.0:7860
    uvicorn.run("app.main:app", host="0.0.0.0", port=7860, reload=False)
