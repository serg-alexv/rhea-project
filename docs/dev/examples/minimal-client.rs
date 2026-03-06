// Minimal: Create a session and add a message
use rhea_client::Client;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Connect to server
    let client = Client::new(
        "http://127.0.0.1:3000",
        "device-1"
    ).await?;

    // Create session
    let session = client.create_session("PROTOS").await?;
    println!("✓ Created session: {}", session);

    // Add message (server assigns Lamport clock)
    let msg_id = client.add_message(&session, "user", "Hello, Rhea!").await?;
    println!("✓ Added message: {}", msg_id);

    // Retrieve messages (ordered by Lamport clock, not wall-clock time)
    let messages = client.get_local_messages(&session).await?;
    println!("\nMessages (ordered by Lamport clock):");
    for (id, role, content, lamport_clock) in messages {
        println!("  [LC:{}] {}: {}", lamport_clock, role, content);
    }

    Ok(())
}
