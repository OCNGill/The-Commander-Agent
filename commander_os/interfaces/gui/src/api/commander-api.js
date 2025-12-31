/**
 * THE COMMANDER: STRATEGIC API CLIENT
 * Handles all communication with the SystemManager REST API.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

class CommanderAPI {
    /**
     * Fetch full cluster status (system, nodes, agents).
     */
    async getSystemStatus() {
        const response = await fetch(`${API_BASE_URL}/system/status`);
        if (!response.ok) throw new Error('Failed to fetch system status');
        return response.json();
    }

    /**
     * List all intelligence nodes.
     */
    async listNodes() {
        const response = await fetch(`${API_BASE_URL}/nodes`);
        if (!response.ok) throw new Error('Failed to list nodes');
        return response.json();
    }

    /**
     * Stop a specific node.
     */
    async stopNode(nodeId) {
        const response = await fetch(`${API_BASE_URL}/nodes/${nodeId}/stop`, { method: 'POST' });
        if (!response.ok) throw new Error('Failed to stop node');
        return response.json();
    }

    /**
     * Reignite a node's engine with new configurations.
     */
    async reigniteNode(nodeId, engineUpdates) {
        const response = await fetch(`${API_BASE_URL}/nodes/${nodeId}/engine`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(engineUpdates)
        });
        if (!response.ok) throw new Error('Failed to reignite node engine');
        return response.json();
    }

    async listModels(nodeId) {
        const response = await fetch(`${API_BASE_URL}/nodes/${nodeId}/models`);
        if (!response.ok) throw new Error('Failed to list models');
        return response.json();
    }

    /**
     * List all active agents.
     */
    async listAgents() {
        const response = await fetch(`${API_BASE_URL}/agents`);
        if (!response.ok) throw new Error('Failed to list agents');
        return response.json();
    }

    /**
     * Ignite or Shutdown a specific node.
     */
    async toggleNode(nodeId, start = true) {
        const action = start ? 'start' : 'stop';
        const response = await fetch(`${API_BASE_URL}/nodes/${nodeId}/${action}`, {
            method: 'POST',
        });
        return response.json();
    }

    /**
     * Ignite the entire cluster.
     */
    async startSystem() {
        const response = await fetch(`${API_BASE_URL}/system/start`, {
            method: 'POST',
        });
        return response.json();
    }

    /**
     * Shutdown the entire cluster.
     */
    async stopSystem() {
        const response = await fetch(`${API_BASE_URL}/system/stop`, {
            method: 'POST',
        });
        return response.json();
    }

    /**
     * Fetch recent traffic from the MessageStore.
     */
    async queryMemory(limit = 20) {
        const response = await fetch(`${API_BASE_URL}/memory/search?limit=${limit}`);
        if (!response.ok) throw new Error('Failed to search memory');
        return response.json();
    }

    async sendCommand(text) {
        const response = await fetch(`${API_BASE_URL}/command`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        if (!response.ok) throw new Error('Failed to send command');
        return response.json();
    }

    /**
   * Subscribe to real-time tactical updates via WebSockets.
   */
    subscribe(onUpdate) {
        const wsUrl = API_BASE_URL.replace('http', 'ws') + '/ws/stream';
        const socket = new WebSocket(wsUrl);

        socket.onopen = () => console.log("Tactics initialized: WebSocket Connected.");
        socket.onmessage = (event) => {
            const packet = JSON.parse(event.data);
            onUpdate(packet);
        };
        socket.onclose = () => {
            console.warn("Tactical link lost. Reconnecting in 5s...");
            setTimeout(() => this.subscribe(onUpdate), 5000);
        };

        return socket;
    }
}

const api = new CommanderAPI();
export default api;
