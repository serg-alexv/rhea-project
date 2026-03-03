# MongoDB Task Queue for Rhea

Mongo replaces the previous SQLite queue so that Fly.io / Atlas can scale horizontally with flexible schema and cloud-native access.

## Cluster setup (Atlas)
1. Create a free Atlas cluster named `rhea` (choose provider/AWS, GCP, or Azure; pick region like `Europe-West`).
2. In **Network Access**, whitelist the IP ranges used by your agents or temporarily `0.0.0.0/0` (dev only).
3. In **Database Access** create a user (`rhea`/strong password) with `readWrite` on the `rhea` database.
4. Copy the connection string (e.g. `mongodb+srv://rhea:<password>@rhea.abc.mongodb.net/?retryWrites=true&w=majority`).
5. Store it in the environment variable `TASK_DB_URI` (local `.env`, Fly secrets, or CLI config). The default code falls back to `mongodb://localhost:27017/rhea` when the variable is missing.

## Local development
- Run `mongod` locally and use the default URI. The queue creates indexes automatically.
- If you want offline failover, keep the old `data/tasks.db` snapshot (or run `TaskDBMongo` with a `sqlite` fallback script).

## Migration tips
- Any existing tasks can be exported from SQLite (`SELECT * FROM tasks`) and inserted as JSON documents into the `tasks` collection.
- The new queue keeps `task_log` as a separate collection for auditing.

## Integration checklist
- Update `tribunal_api.py` / `rhea_executor.py` to import `TaskDBMongo` from `src/task_db_mongo.py`.
- Share `TASK_DB_URI` via Fly secrets or `dotenv` files when deploying.
- Document the new service in the onboarding guide so agents know where to point their configs.

## Why Mongo?
| Scenario | SQLite | MongoDB |
|---|---|---|
| Scaling across machines | ❌ | ✅
| Flexible, nested task metadata | ⚠️ (JSON in text) | ✅ (native BSON)
| High concurrency (multi-agent) | ⚠️ (file locking) | ✅ (findOneAndUpdate with WAL)
| Embedded/mobile prototype | ✅ (zero config) | ⚠️ (requires network)

Mongo is now the primary queue for Fly deployments; keep SQLite only for offline / embedded prototypes where a full database server is not available.
