# Bandwidth-Minimization Architecture

This diagram illustrates the edge-only event-triggered architecture that ensures raw video stays on the bus, and only priority-ordered, compact JSON events are transmitted over the cellular network.

```mermaid
graph TD
    subgraph "On-Board Edge AI (Bus)"
        Cam1[Camera Streams] --> |Raw Video| PD(Pothole Detection)
        Cam1 --> |Raw Video| VD(Vehicle & Pedestrian Detection)
        Cam1 --> |Raw Video| ID(Incident/ANPR Detection)
        
        PD --> |JSON Event| TX(Transmission Module)
        VD --> |JSON Event| TX
        ID --> |JSON Event| TX
        
        TX --> |Buffer & Prioritize| Q[(Local Outbox Queue)]
    end
    
    Q --> |Flush on Network Available| NET((Cellular Network))
    
    subgraph "Central Urban Intelligence Platform"
        NET --> |High Priority First| GW[API Gateway]
        GW --> DB[(Central Event Database)]
        DB --> Dashboard[GIS Dashboard]
    end
    
    style Cam1 fill:#f9f,stroke:#333,stroke-width:2px
    style Q fill:#ff9,stroke:#333,stroke-width:2px
    style NET fill:#9cf,stroke:#333,stroke-width:2px
```

### Key Principles
1. **Edge-only processing**: Video never hits a transmit queue. The AI models consume frames in real-time on the device and discard them.
2. **Event-triggered**: `TransmissionQueue` only fires when an anomaly or count is detected.
3. **Offline Buffering**: Events queue in `outbox/` when connection is lost, preventing data loss.
4. **Priority Ordering**: Incidents (like `incident_hitandrun`) are pulled from the queue and sent before routine infrastructure updates.
