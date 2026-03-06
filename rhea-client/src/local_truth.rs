use sqlx::sqlite::{SqlitePool, SqliteConnectOptions};
use sqlx::Row;
use std::str::FromStr;
use uuid::Uuid;
use chrono::Utc;
use anyhow::Result;

pub struct LocalTruth {
    db: SqlitePool,
}

impl LocalTruth {
    pub async fn new(db_path: &str) -> Result<Self> {
        // Create SQLite connection
        let connect_options = SqliteConnectOptions::from_str(db_path)?
            .create_if_missing(true);

        let pool = sqlx::sqlite::SqlitePoolOptions::new()
            .max_connections(5)
            .connect_with(connect_options)
            .await?;

        // Initialize schema
        sqlx::query(
            "CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                character TEXT NOT NULL,
                title TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                device_id TEXT NOT NULL
            )"
        )
        .execute(&pool)
        .await?;

        sqlx::query(
            "CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                lamport_clock INTEGER NOT NULL,
                device_id TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id),
                UNIQUE(session_id, lamport_clock)
            )"
        )
        .execute(&pool)
        .await?;

        sqlx::query(
            "CREATE TABLE IF NOT EXISTS sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                record_id TEXT NOT NULL,
                operation TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                device_id TEXT NOT NULL
            )"
        )
        .execute(&pool)
        .await?;

        Ok(LocalTruth { db: pool })
    }

    pub async fn add_session(&self, session_id: &str, character: &str, title: &str, device_id: &str) -> Result<()> {
        let now = Utc::now().timestamp();
        
        sqlx::query(
            "INSERT OR IGNORE INTO sessions (id, character, title, created_at, updated_at, device_id) 
             VALUES (?, ?, ?, ?, ?, ?)"
        )
        .bind(session_id)
        .bind(character)
        .bind(title)
        .bind(now)
        .bind(now)
        .bind(device_id)
        .execute(&self.db)
        .await?;

        // Log the sync event
        self.log_sync("sessions", session_id, "INSERT", device_id).await?;

        Ok(())
    }

    pub async fn add_message(&self, msg_id: &str, session_id: &str, role: &str, content: &str, lamport_clock: u64, device_id: &str) -> Result<()> {
        let now = Utc::now().timestamp();
        
        sqlx::query(
            "INSERT OR IGNORE INTO messages (id, session_id, role, content, created_at, lamport_clock, device_id)
             VALUES (?, ?, ?, ?, ?, ?, ?)"
        )
        .bind(msg_id)
        .bind(session_id)
        .bind(role)
        .bind(content)
        .bind(now)
        .bind(lamport_clock as i64)
        .bind(device_id)
        .execute(&self.db)
        .await?;

        // Update session timestamp
        sqlx::query("UPDATE sessions SET updated_at = ? WHERE id = ?")
            .bind(now)
            .bind(session_id)
            .execute(&self.db)
            .await?;

        // Log the sync event
        self.log_sync("messages", msg_id, "INSERT", device_id).await?;

        Ok(())
    }

    pub async fn get_messages(&self, session_id: &str) -> Result<Vec<(String, String, String, u64)>> {
        let rows = sqlx::query(
            "SELECT id, role, content, lamport_clock FROM messages WHERE session_id = ? ORDER BY lamport_clock ASC"
        )
        .bind(session_id)
        .fetch_all(&self.db)
        .await?;

        Ok(rows.iter().map(|row| {
            (
                row.get::<String, _>(0),
                row.get::<String, _>(1),
                row.get::<String, _>(2),
                row.get::<i64, _>(3) as u64,
            )
        }).collect())
    }

    pub async fn get_sessions(&self) -> Result<Vec<(String, String, String)>> {
        let rows = sqlx::query(
            "SELECT id, character, title FROM sessions ORDER BY updated_at DESC"
        )
        .fetch_all(&self.db)
        .await?;

        Ok(rows.iter().map(|row| {
            (
                row.get::<String, _>(0),
                row.get::<String, _>(1),
                row.get::<String, _>(2),
            )
        }).collect())
    }

    pub async fn sync_log(&self, since_timestamp: i64) -> Result<Vec<(String, String, String)>> {
        let rows = sqlx::query(
            "SELECT table_name, record_id, operation FROM sync_log WHERE timestamp > ? ORDER BY timestamp"
        )
        .bind(since_timestamp)
        .fetch_all(&self.db)
        .await?;

        Ok(rows.iter().map(|row| {
            (
                row.get::<String, _>(0),
                row.get::<String, _>(1),
                row.get::<String, _>(2),
            )
        }).collect())
    }

    async fn log_sync(&self, table_name: &str, record_id: &str, operation: &str, device_id: &str) -> Result<()> {
        let now = Utc::now().timestamp();
        
        sqlx::query(
            "INSERT INTO sync_log (table_name, record_id, operation, timestamp, device_id)
             VALUES (?, ?, ?, ?, ?)"
        )
        .bind(table_name)
        .bind(record_id)
        .bind(operation)
        .bind(now)
        .bind(device_id)
        .execute(&self.db)
        .await?;

        Ok(())
    }
}
