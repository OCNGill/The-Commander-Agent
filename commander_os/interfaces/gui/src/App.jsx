import React, { useState, useEffect } from 'react';
import { Shield, Activity, Database, Cpu, Layout, Power, RefreshCw, Terminal } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from './api/commander-api';
import TerminalLog from './components/TerminalLog';
import './App.css';

function App() {
  const [nodes, setNodes] = useState([]);
  const [agents, setAgents] = useState([]);
  const [systemStatus, setSystemStatus] = useState('stopped');
  const [selectedNode, setSelectedNode] = useState(null);
  const [traffic, setTraffic] = useState([]);
  const [loading, setLoading] = useState(true);

  // Subscribe to real-time updates
  useEffect(() => {
    // Initial fetch to populate state
    const fetchInitial = async () => {
      try {
        const nodeList = await api.listNodes();
        setNodes(nodeList);
        const agentList = await api.listAgents(); // Fetch agents initially
        setAgents(agentList);
        const logs = await api.queryMemory(15);
        setTraffic(logs);
      } catch (err) {
        console.error("Initial fetch failed:", err);
      } finally {
        setLoading(false); // Ensure loading is set to false after initial fetch
      }
    };
    fetchInitial();

    // Establish tactical WebSocket link
    const socket = api.subscribe((packet) => {
      if (packet.type === 'state_update') {
        const snapshot = packet.data;
        setSystemStatus(snapshot.system.status);

        // Match nodes with config overlay (we still need listNodes for the name/bench overlay)
        // or we could push the full merged config in state_update. 
        // For now, let's keep it simple and just update the status from snapshot.
        setNodes(prev => prev.map(n => {
          const match = Object.values(snapshot.nodes).find(sn => sn.node_id === n.node_id);
          return match ? { ...n, status: match.status } : n;
        }));
        // Update agents if they are part of the state_update
        if (snapshot.agents) {
          setAgents(snapshot.agents);
        }
      } else if (packet.type === 'new_messages') {
        // Prepend new messages to the log stream
        setTraffic(prev => [...packet.data.reverse(), ...prev].slice(0, 50));
      }
    });

    return () => socket.close();
  }, []);

  const handleIgnite = async () => {
    try {
      if (systemStatus === 'running') {
        await api.stopSystem();
      } else {
        await api.startSystem();
      }
    } catch (err) {
      alert("Ignition sequence failure: " + err.message);
    }
  };

  const isIgnited = systemStatus === 'running';

  return (
    <div className="war-room-root">
      {/* Strategic Header */}
      <header className="strategic-header">
        <div className="logo-section">
          <Shield className="glow-icon" color="var(--accent-cyan)" size={32} />
          <div className="title-block">
            <h1 className="glow-text">THE COMMANDER OS</h1>
            <span className="subtitle">ORCHESTRATION LAYER // PHASE 6 ACTIVE</span>
          </div>
        </div>

        <div className="system-status">
          <div className="status-item">
            <Activity size={18} color="var(--success)" />
            <span>CLUSTER ONLINE</span>
          </div>
          <button
            className={`ignite-button ${isIgnited ? 'active' : ''}`}
            onClick={handleIgnite}
          >
            <Power size={18} />
            {isIgnited ? 'SYSTEM ARMED' : 'IGNITE CLUSTER'}
          </button>
        </div>
      </header>

      {/* Main Command Area */}
      <main className="command-grid">
        <section className="nodes-section">
          <div className="section-header">
            <Layout size={20} />
            <h2>INTELLIGENCE NODES</h2>
          </div>
          <div className="nodes-container">
            {nodes.map(node => (
              <motion.div
                key={node.node_id}
                className={`node-card ${selectedNode?.node_id === node.node_id ? 'active' : ''}`}
                whileHover={{ scale: 1.02 }}
                onClick={() => setSelectedNode(node)}
              >
                <div className="node-info">
                  <div className="node-top">
                    <span className="node-name">{node.name || node.node_id}</span>
                    <span className={`status-badge ${node.status}`}>{node.status}</span>
                  </div>
                  <div className="node-hardware">
                    <Cpu size={14} />
                    <span>{node.resources.gpu || 'Default Hardware'} // {node.tps_benchmark || 0} t/s</span>
                  </div>
                </div>
                <div className="node-gauge">
                  <div className={`gauge-fill ${node.status}`} style={{ width: `${(node.tps_benchmark / 130) * 100}%` }}></div>
                </div>
              </motion.div>
            ))}
          </div>

          <TerminalLog data={traffic} />
        </section>

        <section className="control-section">
          <AnimatePresence mode="wait">
            {selectedNode ? (
              <motion.div
                key={selectedNode.node_id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="control-panel panel-container"
              >
                <div className="panel-header strategic-border">
                  <h3>NODE CONTROL: {selectedNode.name || selectedNode.node_id}</h3>
                </div>

                <div className="control-groups">
                  <div className="control-group">
                    <label>HARDWARE ENGINE DIALS</label>
                    <div className="input-grid">
                      <div className="input-box">
                        <span>CONTEXT SIZE</span>
                        <input type="number" defaultValue={selectedNode.ctx || 4096} />
                      </div>
                      <div className="input-box">
                        <span>GPU LAYERS (NGL)</span>
                        <input type="number" defaultValue={selectedNode.ngl || 32} />
                      </div>
                    </div>
                  </div>

                  <div className="control-group">
                    <label>MODEL ARMORY</label>
                    <div className="model-selector">
                      <Database size={18} />
                      <span>{selectedNode.model_file || 'No Model Loaded'}.gguf</span>
                      <RefreshCw size={14} className="spin-hover" />
                    </div>
                  </div>

                  <div className="action-footer">
                    <button className="apply-button">SAVE & RE-IGNITE</button>
                  </div>
                </div>
              </motion.div>
            ) : (
              <div className="empty-panel panel-container">
                <Terminal size={48} color="var(--border-dim)" />
                <p>SELECT A NODE TO ACCESS COMMAND DIALS</p>
              </div>
            )}
          </AnimatePresence>
        </section>
      </main>

      <footer className="strategic-footer">
        <div className="footer-status">
          <Database size={14} />
          <span>ZFS POOL: ONLINE // /gillsystems_zfs_pool/AI_storage</span>
        </div>
        <div className="version-info">
          v1.2.8 // GILLSYSTEMS STRATEGIC INTEL
        </div>
      </footer>
    </div>
  );
}

export default App;
