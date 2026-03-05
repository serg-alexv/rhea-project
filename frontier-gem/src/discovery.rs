//! AI Nearby Discovery System (Ruliad Discovery)
//!
//! Real-time discovery of available AI providers, models, and nodes.
//! Allows iOS app to see what AI "brains" are available for logic chain execution.

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use tokio::sync::RwLock;
use std::sync::Arc;

/// Discovery version
pub const DISCOVERY_VERSION: &str = "1.0";

/// Node status enumeration
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum NodeStatus {
    Ready,
    Thinking,
    Busy,
    Waiting,
    Offline,
    Error(String),
}

impl std::fmt::Display for NodeStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        match self {
            NodeStatus::Ready => write!(f, "ready"),
            NodeStatus::Thinking => write!(f, "thinking"),
            NodeStatus::Busy => write!(f, "busy"),
            NodeStatus::Waiting => write!(f, "waiting"),
            NodeStatus::Offline => write!(f, "offline"),
            NodeStatus::Error(e) => write!(f, "error: {}", e),
        }
    }
}

/// AI Node representing an available AI provider/model
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AINode {
    pub id: String,
    pub provider: String,
    pub model: String,
    pub status: String,  // Serialized from enum
    pub capabilities: Vec<String>,
    pub context_window: u32,
    pub context_used: u32,
    pub last_activity: DateTime<Utc>,
}

impl AINode {
    pub fn new(
        id: String,
        provider: String,
        model: String,
        status: NodeStatus,
        capabilities: Vec<String>,
        context_window: u32,
        context_used: u32,
    ) -> Self {
        Self {
            id,
            provider,
            model,
            status: format!("{}", status),
            capabilities,
            context_window,
            context_used,
            last_activity: Utc::now(),
        }
    }
}

/// System information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemInfo {
    pub system_focus: String,
    pub focus_window_class: String,
    pub focus_title: String,
    pub timestamp_focus: DateTime<Utc>,
}

impl Default for SystemInfo {
    fn default() -> Self {
        Self {
            system_focus: "Unknown".to_string(),
            focus_window_class: String::new(),
            focus_title: String::new(),
            timestamp_focus: Utc::now(),
        }
    }
}

/// Logic chain state
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChainState {
    pub current_goal: String,
    pub chain_id: String,
    pub node_sequence: Vec<String>,
    pub checkpoint: String,
}

impl Default for ChainState {
    fn default() -> Self {
        Self {
            current_goal: "idle".to_string(),
            chain_id: uuid::Uuid::new_v4().to_string(),
            node_sequence: Vec::new(),
            checkpoint: "awaiting_user_selection".to_string(),
        }
    }
}

/// Daemon metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Metadata {
    pub host: String,
    pub daemon_version: String,
    pub uptime_seconds: u64,
    pub discovery_interval_ms: u32,
}

impl Default for Metadata {
    fn default() -> Self {
        Self {
            host: hostname::get()
                .map(|h| h.to_string_lossy().to_string())
                .unwrap_or_else(|_| "unknown-host".to_string()),
            daemon_version: env!("CARGO_PKG_VERSION").to_string(),
            uptime_seconds: 0,
            discovery_interval_ms: 5000,
        }
    }
}

/// Complete discovery state
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiscoveryState {
    pub timestamp: DateTime<Utc>,
    pub discovery_version: String,
    pub active_nodes: Vec<AINode>,
    pub system_info: SystemInfo,
    pub logic_chain_state: ChainState,
    pub metadata: Metadata,
}

impl Default for DiscoveryState {
    fn default() -> Self {
        Self {
            timestamp: Utc::now(),
            discovery_version: DISCOVERY_VERSION.to_string(),
            active_nodes: Vec::new(),
            system_info: SystemInfo::default(),
            logic_chain_state: ChainState::default(),
            metadata: Metadata::default(),
        }
    }
}

impl DiscoveryState {
    /// Create a new discovery state with example nodes (for testing)
    pub fn with_example_nodes() -> Self {
        let mut state = Self::default();
        
        state.active_nodes = vec![
            AINode::new(
                "tab_01".to_string(),
                "Anthropic".to_string(),
                "Claude 3.5 Sonnet".to_string(),
                NodeStatus::Ready,
                vec![
                    "text_injection".to_string(),
                    "reasoning".to_string(),
                    "code_generation".to_string(),
                ],
                200000,
                45000,
            ),
            AINode::new(
                "tab_02".to_string(),
                "OpenAI".to_string(),
                "GPT-4o".to_string(),
                NodeStatus::Thinking,
                vec![
                    "vision".to_string(),
                    "text_injection".to_string(),
                    "reasoning".to_string(),
                ],
                128000,
                89000,
            ),
        ];

        state.system_info = SystemInfo {
            system_focus: "Telegram.exe".to_string(),
            focus_window_class: "QXcbWindow".to_string(),
            focus_title: "Telegram: Rhea Project Chat".to_string(),
            timestamp_focus: Utc::now(),
        };

        state.logic_chain_state = ChainState {
            current_goal: "negotiate_api_access".to_string(),
            chain_id: uuid::Uuid::new_v4().to_string(),
            node_sequence: vec!["tab_01".to_string(), "tab_02".to_string()],
            checkpoint: "awaiting_user_selection".to_string(),
        };

        state
    }

    /// Convert to JSON string
    pub fn to_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string(self)
    }

    /// Convert to pretty JSON string
    pub fn to_json_pretty(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string_pretty(self)
    }

    /// Add or update a node
    pub fn add_node(&mut self, node: AINode) {
        if let Some(existing) = self.active_nodes.iter_mut().find(|n| n.id == node.id) {
            *existing = node;
        } else {
            self.active_nodes.push(node);
        }
    }

    /// Update node status
    pub fn set_node_status(&mut self, node_id: &str, status: NodeStatus) {
        if let Some(node) = self.active_nodes.iter_mut().find(|n| n.id == node_id) {
            node.status = format!("{}", status);
            node.last_activity = Utc::now();
        }
    }

    /// Update logic chain goal
    pub fn set_goal(&mut self, goal: String) {
        self.logic_chain_state.current_goal = goal;
        self.timestamp = Utc::now();
    }

    /// Update node sequence
    pub fn set_node_sequence(&mut self, sequence: Vec<String>) {
        self.logic_chain_state.node_sequence = sequence;
        self.timestamp = Utc::now();
    }

    /// Update checkpoint
    pub fn set_checkpoint(&mut self, checkpoint: String) {
        self.logic_chain_state.checkpoint = checkpoint;
        self.timestamp = Utc::now();
    }
}

/// Discovery engine with caching
pub struct DiscoveryEngine {
    state: Arc<RwLock<DiscoveryState>>,
    last_update: Arc<RwLock<DateTime<Utc>>>,
}

impl DiscoveryEngine {
    /// Create a new discovery engine
    pub fn new() -> Self {
        Self {
            state: Arc::new(RwLock::new(DiscoveryState::default())),
            last_update: Arc::new(RwLock::new(Utc::now())),
        }
    }

    /// Get current discovery state
    pub async fn get_state(&self) -> DiscoveryState {
        self.state.read().await.clone()
    }

    /// Update entire state
    pub async fn update_state(&self, new_state: DiscoveryState) {
        let mut state = self.state.write().await;
        *state = new_state;
        *self.last_update.write().await = Utc::now();
    }

    /// Add or update a node
    pub async fn add_node(&self, node: AINode) {
        let mut state = self.state.write().await;
        state.add_node(node);
        state.timestamp = Utc::now();
    }

    /// Update node status
    pub async fn set_node_status(&self, node_id: &str, status: NodeStatus) {
        let mut state = self.state.write().await;
        state.set_node_status(node_id, status);
    }

    /// Set current logic goal
    pub async fn set_goal(&self, goal: String) {
        let mut state = self.state.write().await;
        state.set_goal(goal);
    }

    /// Set node sequence
    pub async fn set_sequence(&self, sequence: Vec<String>) {
        let mut state = self.state.write().await;
        state.set_node_sequence(sequence);
    }

    /// Get ready nodes (can accept injection)
    pub async fn get_ready_nodes(&self) -> Vec<AINode> {
        let state = self.state.read().await;
        state
            .active_nodes
            .iter()
            .filter(|n| n.status == "ready")
            .cloned()
            .collect()
    }

    /// Get nodes by provider
    pub async fn get_nodes_by_provider(&self, provider: &str) -> Vec<AINode> {
        let state = self.state.read().await;
        state
            .active_nodes
            .iter()
            .filter(|n| n.provider.eq_ignore_ascii_case(provider))
            .cloned()
            .collect()
    }

    /// Check if node exists
    pub async fn has_node(&self, node_id: &str) -> bool {
        let state = self.state.read().await;
        state.active_nodes.iter().any(|n| n.id == node_id)
    }

    /// Remove offline node
    pub async fn remove_offline_node(&self, node_id: &str) {
        let mut state = self.state.write().await;
        state.active_nodes.retain(|n| n.id != node_id);
    }
}

impl Default for DiscoveryEngine {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_discovery_state_creation() {
        let state = DiscoveryState::default();
        assert_eq!(state.discovery_version, DISCOVERY_VERSION);
        assert!(state.active_nodes.is_empty());
    }

    #[test]
    fn test_discovery_with_example_nodes() {
        let state = DiscoveryState::with_example_nodes();
        assert_eq!(state.active_nodes.len(), 2);
        assert_eq!(state.active_nodes[0].provider, "Anthropic");
        assert_eq!(state.active_nodes[1].provider, "OpenAI");
    }

    #[test]
    fn test_node_serialization() {
        let state = DiscoveryState::with_example_nodes();
        let json = state.to_json().unwrap();
        assert!(json.contains("Claude 3.5 Sonnet"));
        assert!(json.contains("GPT-4o"));
    }

    #[tokio::test]
    async fn test_discovery_engine_add_node() {
        let engine = DiscoveryEngine::new();
        let node = AINode::new(
            "test_01".to_string(),
            "TestProvider".to_string(),
            "TestModel".to_string(),
            NodeStatus::Ready,
            vec!["test".to_string()],
            100000,
            0,
        );

        engine.add_node(node.clone()).await;
        let state = engine.get_state().await;
        assert_eq!(state.active_nodes.len(), 1);
        assert_eq!(state.active_nodes[0].id, "test_01");
    }

    #[tokio::test]
    async fn test_discovery_engine_get_ready_nodes() {
        let engine = DiscoveryEngine::new();
        engine
            .add_node(AINode::new(
                "ready_01".to_string(),
                "Provider1".to_string(),
                "Model1".to_string(),
                NodeStatus::Ready,
                vec![],
                100000,
                0,
            ))
            .await;
        engine
            .add_node(AINode::new(
                "busy_01".to_string(),
                "Provider2".to_string(),
                "Model2".to_string(),
                NodeStatus::Busy,
                vec![],
                100000,
                0,
            ))
            .await;

        let ready = engine.get_ready_nodes().await;
        assert_eq!(ready.len(), 1);
        assert_eq!(ready[0].id, "ready_01");
    }
}
