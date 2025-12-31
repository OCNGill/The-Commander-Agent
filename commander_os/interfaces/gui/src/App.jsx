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
  const [dials, setDials] = useState({ ctx: 4096, ngl: 32, fa: true, binary: 'go.exe' });
  const [availableModels, setAvailableModels] = useState([]);
  const selectedNodeRef = React.useRef(null);

  const handleSelectNode = (node) => {
    setSelectedNode(node);
    selectedNodeRef.current = node;
  };

  // Establish tactical WebSocket link
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

    const socket = api.subscribe((packet) => {
      if (packet.type === 'state_update') {
        const snapshot = packet.data;
        setSystemStatus(snapshot.system.status);

        setNodes(prev => {
          return prev.map(n => {
            const match = Object.values(snapshot.nodes).find(sn => sn.node_id === n.node_id);
            if (match) {
              return { ...n, ...match, status: match.status };
            }
            return n;
          });
        });

        // Update selectedNode directly if it exists in snapshot using ref to stay current
        if (selectedNodeRef.current) {
          const match = Object.values(snapshot.nodes).find(sn => sn.node_id === selectedNodeRef.current.node_id);
          if (match) {
            setSelectedNode(prev => prev ? { ...prev, ...match, status: match.status } : null);
          }
        }

        if (snapshot.agents) {
          setAgents(snapshot.agents);
        }
      } else if (packet.type === 'new_messages') {
        setTraffic(prev => [...packet.data.reverse(), ...prev].slice(0, 50));
      }
    });

    return () => socket.close();
  }, []);

  // Sync dials and models when selectedNode changes
  useEffect(() => {
    if (selectedNode) {
      setDials({
        ctx: selectedNode.ctx || 4096,
        ngl: selectedNode.ngl || 32,
        fa: selectedNode.fa !== undefined ? selectedNode.fa : true,
        binary: selectedNode.model_file ? (selectedNode.binary || 'go.exe') : (selectedNode.binary || 'go.exe')
      });

      // Fetch models for this node
      api.listModels(selectedNode.node_id)
        .then(setAvailableModels)
        .catch(err => console.error("Failed to load models for node:", err));
    }
  }, [selectedNode]);

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

  const handleSaveDials = async () => {
    if (!selectedNode) return;
    try {
      const updates = {
        ...dials,
        model_file: selectedNode.model_file
      };
      await api.reigniteNode(selectedNode.node_id, updates);
      alert(`Tactical Re-Ignition Successful: ${selectedNode.node_id} optimized.`);
    } catch (err) {
      alert("Hardware dial adjustment failed: " + err.message);
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
                onClick={() => handleSelectNode(node)}
              >
                <div className="node-info">
                  <div className="node-top">
                    <span className="node-name">{node.name || node.node_id}</span>
                    <span className={`status-badge ${node.status}`}>{node.status}</span>
                  </div>
                  <div className="node-hardware">
                    <Cpu size={14} />
                    <span>{node.metrics?.tps?.toFixed(1) || '0.0'} TPS // {node.tps_benchmark || 0} MAX</span>
                  </div>
                </div>
                <div className="node-gauge">
                  <div className={`gauge-fill ${node.status}`} style={{ width: `${Math.min(100, (node.metrics?.tps / (node.tps_benchmark || 100)) * 100)}%` }}></div>
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

                <div className="telemetry-strip">
                  <div className="telemetry-item">
                    <span className="label">LIVE PERFORMANCE</span>
                    <span className="value glow-text">{(selectedNode.metrics?.tps || 0).toFixed(2)} TPS</span>
                  </div>
                  <div className="telemetry-item">
                    <span className="label">LOAD</span>
                    <span className="value">{(selectedNode.metrics?.load || 0).toFixed(1)}%</span>
                  </div>
                  <div className="telemetry-item">
                    <span className="label">NODE UPTIME</span>
                    <span className="value">{selectedNode.registration_time ? ((Date.now() / 1000 - selectedNode.registration_time) / 3600).toFixed(1) : '0.0'}h</span>
                  </div>
                </div>

                <div className="control-groups">
                  <div className="control-group">
                    <label>HARDWARE ENGINE DIALS</label>
                    <div className="input-grid">
                      <div className="input-box">
                        <span>CONTEXT SIZE</span>
                        <input
                          type="number"
                          value={dials.ctx}
                          onChange={(e) => setDials({ ...dials, ctx: parseInt(e.target.value) })}
                        />
                      </div>
                      <div className="input-box">
                        <span>GPU LAYERS (NGL)</span>
                        <input
                          type="number"
                          value={dials.ngl}
                          onChange={(e) => setDials({ ...dials, ngl: parseInt(e.target.value) })}
                        />
                      </div>
                      <div className="input-box toggle-box">
                        <span>FLASH ATTN</span>
                        <button
                          className={`toggle-btn ${dials.fa ? 'active' : ''}`}
                          onClick={() => setDials({ ...dials, fa: !dials.fa })}
                        >
                          {dials.fa ? 'ON' : 'OFF'}
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="control-group">
                    <label>BINARY AUTHORITY</label>
                    <div className="input-box">
                      <input
                        type="text"
                        value={dials.binary}
                        onChange={(e) => setDials({ ...dials, binary: e.target.value })}
                        placeholder="e.g. go.exe"
                      />
                      <span className="input-hint">Specify the backend binary for ignition.</span>
                    </div>
                  </div>

                  <div className="control-group">
                    <label>MODEL ARMORY</label>
                    <div className="model-select-wrapper">
                      <Database size={18} />
                      <select
                        className="strategic-select"
                        value={selectedNode.model_file}
                        onChange={(e) => {
                          const newModel = e.target.value;
                          const updatedNode = { ...selectedNode, model_file: newModel };
                          setSelectedNode(updatedNode);
                        }}
                      >
                        <option value={selectedNode.model_file}>{selectedNode.model_file}</option>
                        {availableModels.filter(m => m !== selectedNode.model_file).map(m => (
                          <option key={m} value={m}>{m}</option>
                        ))}
                      </select>
                      <RefreshCw size={14} className="spin-hover" />
                    </div>
                  </div>

                  <div className="action-footer">
                    <button className="apply-button" onClick={handleSaveDials}>SAVE & RE-IGNITE</button>
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
