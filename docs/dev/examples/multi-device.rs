// Multi-Device Sync: Show devices converging on the same message order
use rhea_client::Client;
use std::time::Duration;
use tokio::time::sleep;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Create two clients (different devices)
    let device1 = Client::new(
        "http://127.0.0.1:3000",
        "device-1"
    ).await?;

    let device2 = Client::new(
        "http://127.0.0.1:3000",
        "device-2"
    ).await?;

    // Device 1 creates a session
    let session = device1.create_session("PROTOS").await?;
    println!("Device 1 created session: {}", session);

    // Device 1 adds messages
    println!("\n[Device 1] Adding messages...");
    device1.add_message(&session, "user", "Hello from Device 1").await?;
    device1.add_message(&session, "assistant", "Response from Device 1").await?;

    // Device 2 adds messages (to same session)
    println!("[Device 2] Adding messages...");
    device2.add_message(&session, "user", "Hello from Device 2").await?;

    // Small delay for server to process
    sleep(Duration::from_millis(100)).await;

    // Both devices retrieve messages
    println!("\n[Device 1] Messages:");
    let msgs1 = device1.get_local_messages(&session).await?;
    for (_, role, content, lc) in &msgs1 {
        println!("  [LC:{}] {}: {}", lc, role, content);
    }

    println!("\n[Device 2] Messages:");
    let msgs2 = device2.get_local_messages(&session).await?;
    for (_, role, content, lc) in &msgs2 {
        println!("  [LC:{}] {}: {}", lc, role, content);
    }

    // Verify convergence
    println!("\n✓ Convergence check:");
    if msgs1.len() == msgs2.len() {
        println!("  ✓ Both devices have {} messages", msgs1.len());
    }
    let all_match = msgs1.iter().zip(msgs2.iter()).all(
        |(m1, m2)| m1.0 == m2.0 && m1.3 == m2.3
    );
    if all_match {
        println!("  ✓ Message order is identical on both devices");
        println!("  ✓ **Devices converged!**");
    }

    Ok(())
}
