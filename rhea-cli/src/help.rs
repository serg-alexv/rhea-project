pub fn show_task_guide() {
    println!("\n🎯 RHEA TASK DEFINITION GUIDE\n");
    println!("A TASK has clear boundaries. A prompt is just talking.\n");
    
    println!("✅ TASK EXAMPLES:");
    println!("  • 'Add SQLite to rhea-session-server'");
    println!("    What: Store sessions in DB (not RAM)");
    println!("    Done when: Sessions survive app restart\n");
    
    println!("  • 'Implement message dedup in sync'");
    println!("    What: UUID-based dedup when merging");
    println!("    Done when: Test shows no duplicates\n");
    
    println!("❌ NOT TASKS:");
    println!("  • 'Make it better' (vague, no endpoint)");
    println!("  • 'How should we do X?' (question, not task)");
    println!("  • 'Explore CRDT options' (exploration, not task)\n");
    
    println!("📋 TASK TEMPLATE:");
    println!("  What:     [One sentence]");
    println!("  Where:    [Which file/module]");
    println!("  Done when: [How you know it's done]");
    println!("  Test:     [What passes to confirm]\n");
    
    println!("Rule: If you can't write a test for it, it's not a task yet.\n");
}

pub fn show_help() {
    println!("\n🌟 RHEA CHAT CLI - Cross-Device Sessions\n");
    println!("USAGE:");
    println!("  rhea-cli [options]\n");
    
    println!("COMMANDS:");
    println!("  [1-4]     Select character (Protos/Zerg/Terran/Aeon)");
    println!("  [text]    Type message");
    println!("  Enter     Send message");
    println!("  Esc       Back / Quit");
    println!("  Ctrl+C    Quit\n");
    
    println!("OPTIONS:");
    println!("  --help            Show this help");
    println!("  --task-guide      Show task definition rules");
    println!("  --device-id       Show your device ID");
    println!("  --db <path>       Use custom SQLite DB\n");
    
    println!("ABOUT:");
    println!("  Each device has local SQLite (your truth).");
    println!("  Sessions sync via HTTP to server.");
    println!("  Messages deduplicate by UUID (CRDT).\n");
}
