### Docker

Build image
```
docker build -t punctual/streamlit:1.0 .
```

Run
```
docker run -d -p 8501:8501 punctual/streamlit:1.0

docker run -d -p 8501:8501 --env PUNCTUAL_MAPBOX_TOKEN=$Env:PUNCTUAL_MAPBOX_TOKEN --env PUNCTUAL_OPENAI_TOKEN=$Env:PUNCTUAL_OPENAI_TOKEN punctual/streamlit:1.0
```