use reqwest::Client;
use rhea_session_server::{
    Session, Character, CreateSessionRequest, AddMessageRequest, 
    GetSessionResponse, SessionResponse, Message,
};
use uuid::Uuid;

pub mod local_truth;
pub use local_truth::LocalTruth;

pub struct RheaClient {
    server_url: String,
    http_client: Client,
    current_session_id: Option<Uuid>,
    local_truth: LocalTruth,
    device_id: String,
}

impl RheaClient {
    pub async fn new(server_url: String, db_path: &str) -> Result<Self, anyhow::Error> {
        let local_truth = LocalTruth::new(db_path).await?;
        let device_id = uuid::Uuid::new_v4().to_string();

        Ok(RheaClient {
            server_url,
            http_client: Client::new(),
            current_session_id: None,
            local_truth,
            device_id,
        })
    }

    pub async fn create_session(&mut self, character: Character) -> Result<SessionResponse, String> {
        let url = format!("{}/sessions", self.server_url);
        let req = CreateSessionRequest { character: character.clone() };

        let resp = self.http_client
            .post(&url)
            .json(&req)
            .send()
            .await
            .map_err(|e| e.to_string())?;

        let session = resp
            .json::<SessionResponse>()
            .await
            .map_err(|e| e.to_string())?;

        // Store locally
        self.local_truth
            .add_session(&session.id.to_string(), &character.name(), &session.title, &self.device_id)
            .await
            .map_err(|e| e.to_string())?;

        self.current_session_id = Some(session.id);
        Ok(session)
    }

    pub async fn get_session(&self, id: Uuid) -> Result<GetSessionResponse, String> {
        let url = format!("{}/sessions/{}", self.server_url, id);

        let resp = self.http_client
            .get(&url)
            .send()
            .await
            .map_err(|e| e.to_string())?;

        resp.json::<GetSessionResponse>()
            .await
            .map_err(|e| e.to_string())
    }

    pub async fn list_sessions(&self) -> Result<Vec<SessionResponse>, String> {
        let url = format!("{}/sessions", self.server_url);

        let resp = self.http_client
            .get(&url)
            .send()
            .await
            .map_err(|e| e.to_string())?;

        resp.json::<Vec<SessionResponse>>()
            .await
            .map_err(|e| e.to_string())
    }

    pub async fn add_message(
        &self,
        session_id: Uuid,
        role: String,
        content: String,
    ) -> Result<Uuid, String> {
        let url = format!("{}/sessions/{}/messages", self.server_url, session_id);
        let req = AddMessageRequest { role, content };

        let resp = self.http_client
            .post(&url)
            .json(&req)
            .send()
            .await
            .map_err(|e| e.to_string())?;

        let body = resp
            .json::<serde_json::Value>()
            .await
            .map_err(|e| e.to_string())?;

        let id = body["id"]
            .as_str()
            .ok_or("No ID in response".to_string())?
            .parse::<Uuid>()
            .map_err(|e| e.to_string())?;

        let lamport_clock = body["lamport_clock"]
            .as_u64()
            .ok_or("No lamport_clock in response".to_string())?;

        // Store locally
        self.local_truth
            .add_message(
                &id.to_string(),
                &session_id.to_string(),
                &req.role,
                &req.content,
                lamport_clock,
                &self.device_id,
            )
            .await
            .map_err(|e| e.to_string())?;

        Ok(id)
    }

    pub async fn get_local_messages(&self, session_id: &str) -> Result<Vec<(String, String, String, u64)>, String> {
        self.local_truth
            .get_messages(session_id)
            .await
            .map_err(|e| e.to_string())
    }

    pub async fn get_local_sessions(&self) -> Result<Vec<(String, String, String)>, String> {
        self.local_truth
            .get_sessions()
            .await
            .map_err(|e| e.to_string())
    }

    pub fn set_session(&mut self, id: Uuid) {
        self.current_session_id = Some(id);
    }

    pub fn current_session(&self) -> Option<Uuid> {
        self.current_session_id
    }

    pub fn device_id(&self) -> &str {
        &self.device_id
    }
}
