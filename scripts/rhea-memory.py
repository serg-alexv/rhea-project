import redis
import json

r = redis.Redis(host='localhost', port=6379, db=0)

def save_context(key, data):
    # Чтобы я не тупил, где лежат твои папки
    r.set(f"rhea:context:{key}", json.dumps(data))

# Записываем твои победы за сегодня
save_context("volumes", {
    "RheaCloud": "/Volumes/RheaCloud",
    "Share": "/Volumes/Share",
    "anotherRhea": "~/anotherRhea"
})

print("✅ Память обновлена. Теперь я не забуду про подрочить)