# Developer Guide: Extending The-Commander

## **Architecture Overview**
The-Commander is a hybrid Python/React application.
- **Backend (Python)**: Handles hardware orchestration, cluster networking, and persistent storage.
- **Frontend (React)**: Handles strategic visualization and user command routing.

## **1. Backend Extension (REST API)**
The Hub resides in `commander_os/interfaces/rest_api.py`.
- **Adding an Endpoint**: Use FastAPI decorators. Always return a Pydantic model or `ActionResponse`.
- **Background Tasks**: Long-running operations (like telemetry or broadcasting) should be handled via `asyncio` loops in `rest_api.py` or `threading.Thread` in `SystemManager`.

## **2. Strategic GUI Components**
The GUI is located in `commander_os/interfaces/gui/src/`.
- **Adding a View**: Create a new `.jsx` component in `./components`. Use **Framer Motion** for tactical transitions.
- **Global Styles**: Update `App.css` to maintain the "War Room" aesthetic (Dark mode, Cyan/Gold accents, Glow effects).
- **Icons**: Use the `lucide-react` library.

## **3. Real-time Telemetry (WebSockets)**
Updates are pushed through `ConnectionManager.broadcast()`.
- **Packet Structure**:
  ```json
  {
    "type": "event_type",
    "data": { ... }
  }
  ```
- **Broadcasting Frequency**: Managed in `broadcast_tactical_updates` inside `rest_api.py`. Currently set to ~2s for telemetry snapshots.

## **4. Core Logic (System Manager)**
When adding new hardware capabilities:
1.  Update `ConfigManager.EngineConfig` in `commander_os/core/config_manager.py`.
2.  Add the logic to `SystemManager._ignite_hardware_engine` in `commander_os/core/system_manager.py`.
3.  Expose the control via `EngineUpdate` Pydantic model in `rest_api.py`.

## **5. Testing Standards**
- **Unit Tests**: Use `pytest`. Test individual managers in `tests/core/`.
- **API Tests**: Mock the `SystemManager` where possible to test endpoint logic.
- **Integration Tests**: Verify the full loop from REST request -> Config Update -> Process Spawn.

## **6. Versioning & Documentation**
Follow the **7D Agile** standard. Every major feature addition requires:
- A version bump in `master_plan.md`.
- Updated documentation in `docs/`.
- A new version of relevant diagrams in `diagrams/`.
