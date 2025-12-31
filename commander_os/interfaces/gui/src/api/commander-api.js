/**
 * THE COMMANDER: STRATEGIC API CLIENT
 * Handles all communication with the SystemManager REST API.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
}

export const api = new CommanderAPI();
