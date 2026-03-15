/**
 * RHEA RUNTIME CORE (runtime.js)
 * The "Kernel" of the JS environment.
 */

globalThis.Rhea = {
    version: "1.0.0-modular",
    plugins: {},
    
    // Minimal registration system
    registerPlugin: function(name, plugin) {
        console.log("Rhea: Registering plugin [" + name + "]");
        this.plugins[name] = plugin;
        if (plugin.init) {
            try {
                plugin.init();
            } catch (e) {
                console.error("Rhea: Plugin [" + name + "] init failed: " + e);
            }
        }
    },
    
    // Telemetry helper
    log: function(msg) {
        console.log("Rhea[Core]: " + msg);
    }
};

Rhea.log("Runtime bootstrap complete.");
