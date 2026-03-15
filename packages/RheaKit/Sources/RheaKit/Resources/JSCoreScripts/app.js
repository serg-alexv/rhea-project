/**
 * RHEA APP PLUGIN (app.js)
 * The first executable "plugin" environment.
 */

if (globalThis.Rhea) {
    Rhea.registerPlugin("app", {
        init: function() {
            Rhea.log("Application plugin starting...");
            Rhea.log("Current version: " + Rhea.version);
            
            // Minimal demo logic
            this.startTime = Date.now();
            console.log("App: Initialization complete at " + this.startTime);
        },
        
        status: function() {
            return "running";
        }
    });
} else {
    console.error("App: Fatal - Rhea Kernel not found.");
}
