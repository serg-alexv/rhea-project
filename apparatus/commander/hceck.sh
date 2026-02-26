# 1. Посмотри логи LiteLLM — там будет причина
docker logs rhea-litellm

# 2. Если контейнер уже мёртв, запусти вручную без health check чтобы увидеть ошибку:
docker run --rm -it \
  -v $(pwd)/litellm_config.yaml:/app/config.yaml:ro \
  --env-file .env \
  ghcr.io/berriai/litellm:main-latest \
  --config /app/config.yaml --detailed_debug
