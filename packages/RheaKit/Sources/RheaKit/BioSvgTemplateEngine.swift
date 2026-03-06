import Foundation

/// A pure-Swift engine to generate SVG representations of biological molecules.
/// Currently focuses on metadata and structural frames to accompany PNG snapshots.
public struct BioSvgTemplateEngine {
    
    /// Generates a structured SVG string containing molecule metadata.
    public static func generateSvg(
        id: String,
        isSmiles: Bool,
        title: String?,
        method: String?,
        resolution: String?,
        organism: String?,
        renderStyle: String,
        colorScheme: String
    ) -> String {
        let label = isSmiles ? "SMILES: \(id)" : "PDB: \(id)"
        let displayTitle = title ?? "Molecular Structure"
        let timestamp = ISO8601DateFormatter().string(from: Date())
        
        // Sanitize strings for XML
        let safeID = id.xmlEscaped
        let safeTitle = displayTitle.xmlEscaped
        let safeMethod = (method ?? "Unknown").xmlEscaped
        let safeResolution = (resolution ?? "N/A").xmlEscaped
        let safeOrganism = (organism ?? "Unknown").xmlEscaped
        
        return """
        <svg width="800" height="600" viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg">
            <!-- Background -->
            <rect width="800" height="600" fill="#0f0f1a"/>
            
            <!-- Frame -->
            <rect x="10" y="10" width="780" height="580" rx="8" stroke="#333344" stroke-width="1" fill="none"/>
            
            <!-- Header -->
            <text x="30" y="50" font-family="monospace" font-size="24" font-weight="bold" fill="#66d9ff">\(safeID)</text>
            <text x="30" y="80" font-family="monospace" font-size="16" fill="#ffffff" opacity="0.8">\(safeTitle)</text>
            
            <!-- Metadata Grid -->
            <g transform="translate(30, 120)">
                <text x="0" y="0" font-family="monospace" font-size="11" fill="#888899">METHOD</text>
                <text x="0" y="18" font-family="monospace" font-size="13" fill="#a6e22e">\(safeMethod)</text>
                
                <text x="200" y="0" font-family="monospace" font-size="11" fill="#888899">RESOLUTION</text>
                <text x="200" y="18" font-family="monospace" font-size="13" fill="#fd971f">\(safeResolution) Å</text>
                
                <text x="0" y="50" font-family="monospace" font-size="11" fill="#888899">ORGANISM</text>
                <text x="0" y="68" font-family="monospace" font-size="13" fill="#ae81ff">\(safeOrganism)</text>
                
                <text x="200" y="50" font-family="monospace" font-size="11" fill="#888899">STYLE / COLOR</text>
                <text x="200" y="68" font-family="monospace" font-size="13" fill="#66d9ff">\(renderStyle.uppercased()) / \(colorScheme.uppercased())</text>
            </g>
            
            <!-- Structural Placeholder -->
            <g transform="translate(400, 350)" opacity="0.15">
                <circle cx="0" cy="0" r="120" stroke="#66d9ff" stroke-width="1" fill="none" stroke-dasharray="4,4"/>
                <path d="M-60,0 L60,0 M0,-60 L0,60" stroke="#66d9ff" stroke-width="0.5"/>
                <text x="0" y="5" font-family="monospace" font-size="10" fill="#66d9ff" text-anchor="middle">RHEA BIO-RENDERER ENGINE</text>
            </g>
            
            <!-- Footer -->
            <rect x="10" y="560" width="780" height="30" rx="4" fill="#1a1a2e"/>
            <text x="30" y="580" font-family="monospace" font-size="10" fill="#ffffff" opacity="0.4">PROPRIETARY RHEA VECTOR FORMAT • \(timestamp)</text>
            <text x="770" y="580" font-family="monospace" font-size="10" fill="#66d9ff" text-anchor="end" opacity="0.6">SECURE SYNC ACTIVE</text>
        </svg>
        """
    }
}

private extension String {
    var xmlEscaped: String {
        return self
            .replacingOccurrences(of: "&", with: "&amp;")
            .replacingOccurrences(of: "<", with: "&lt;")
            .replacingOccurrences(of: ">", with: "&gt;")
            .replacingOccurrences(of: "\"", with: "&quot;")
            .replacingOccurrences(of: "'", with: "&apos;")
    }
}
