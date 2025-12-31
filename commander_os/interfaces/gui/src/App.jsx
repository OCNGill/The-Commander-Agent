import React, { useState, useEffect } from 'react';
import { Terminal, Database, Shield, Zap, Cpu, Activity, Settings, RefreshCw, Power, Layout, BarChart3, Radio } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from './api/commander-api';
import CommanderChat from './components/CommanderChat';
import DeploymentHUD from './components/DeploymentHUD';
import './App.css';

function App() {
  const [nodes, setNodes] = useState([]);
  const [agents, setAgents] = useState([]);
  const [systemStatus, setSystemStatus] = useState('stopped');
  const [selectedNode, setSelectedNode] = useState(null);
  const [traffic, setTraffic] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dials, setDials] = useState({ ctx: 4096, ngl: 32, fa: true, binary: 'go.exe', model_file: '' });
  const [availableModels, setAvailableModels] = useState([]);
  const [apiError, setApiError] = useState(null);
  const [systemVersion, setSystemVersion] = useState('1.2.19');
  const [activeTab, setActiveTab] = useState('control');
  const [chatStats, setChatStats] = useState({ node: 'None', model: 'N/A', context: '0/0', output: 0, toksPerSec: 0.0 });
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
        // Fetch version first
        try {
          const versionInfo = await api.getVersion();
          setSystemVersion(versionInfo.version);
        } catch (e) {
          console.warn("Version fetch failed, using default");
        }
        const nodeList = await api.listNodes();
        setNodes(nodeList);
        const agentList = await api.listAgents();
        setAgents(agentList);
        const logs = await api.queryMemory(15);
        setTraffic(logs);
      } catch (err) {
        console.error("Initial fetch failed:", err);
        setApiError("STRATEGIC LINK FAILURE: THE HUB IS UNREACHABLE");
      } finally {
        setLoading(false);
      }
    };
    fetchInitial();

    const socket = api.subscribe((packet) => {
      if (packet.type === 'state_update') {
        const snapshot = packet.data;
        setSystemStatus(snapshot.system.status);

        // INTELLIGENT NODE MERGE: Ensure we capture NEW nodes from the snapshot
        setNodes(prev => {
          const snapshotNodes = Object.values(snapshot.nodes);
          // We map over the SNAPSHOT (Source of Truth), merging any local UI state from 'prev'
          return snapshotNodes.map(sn => {
            const existing = prev.find(p => p.node_id === sn.node_id);
            return existing ? { ...existing, ...sn } : sn;
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
        // Deduplicate messages by ID before adding
        setTraffic(prev => {
          const newMsgs = packet.data.reverse();
          const existingIds = new Set(prev.map(m => m.id));
          const uniqueNew = newMsgs.filter(m => !existingIds.has(m.id));
          return [...uniqueNew, ...prev].slice(0, 50);
        });
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
        binary: selectedNode.binary || 'go.exe',
        model_file: selectedNode.model_file || ''
      });

      // Update chat stats
      setChatStats({
        node: selectedNode.name || selectedNode.node_id,
        model: selectedNode.model_file || 'N/A',
        context: `0/${selectedNode.ctx || 4096}`,
        output: 0,
        toksPerSec: selectedNode.metrics?.tps || 0.0
      });

      // Fetch models for this node
      api.listModels(selectedNode.node_id)
        .then(models => {
          console.log(`Loaded ${models.length} models for ${selectedNode.node_id}:`, models);
          setAvailableModels(models);
        })
        .catch(err => console.error("Failed to load models for node:", err));
    } else {
      // No node selected - reset chat stats
      setChatStats({ node: 'None', model: 'N/A', context: '0/0', output: 0, toksPerSec: 0.0 });
    }
  }, [selectedNode?.node_id]);

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

  const handleShutdown = async () => {
    if (confirm("WARNING: This will kill all agents and nodes. Proceed?")) {
      try {
        await api.stopSystem();
      } catch (err) {
        alert("Shutdown failed: " + err.message);
      }
    }
  };

  const handleStopNode = async () => {
    if (!selectedNode) return;
    try {
      await api.stopNode(selectedNode.node_id);
    } catch (err) {
      alert("Failed to stop node: " + err.message);
    }
  };

  const handleSaveDials = async () => {
    if (!selectedNode) return;
    try {
      const updates = {
        ctx: dials.ctx,
        ngl: dials.ngl,
        fa: dials.fa,
        binary: dials.binary,
        model_file: dials.model_file
      };
      await api.reigniteNode(selectedNode.node_id, updates);
      alert(`Tactical Re-Ignition Successful: ${selectedNode.node_id} optimized.`);
    } catch (err) {
      alert("Hardware dial adjustment failed: " + err.message);
    }
  };

  const handleCommand = async (text) => {
    try {
      await api.sendCommand(text);
      
      // Update chat stats to reflect the commanding node
      // Find highest-ranking active node
      const activeNodes = nodes.filter(n => n.status === 'ready' || n.status === 'online');
      if (activeNodes.length > 0) {
        activeNodes.sort((a, b) => (b.tps_benchmark || 0) - (a.tps_benchmark || 0));
        const commandingNode = activeNodes[0];
        setChatStats({
          node: commandingNode.name || commandingNode.node_id,
          model: commandingNode.model_file || 'N/A',
          context: `0/${commandingNode.ctx || 4096}`,
          output: 0,
          toksPerSec: commandingNode.metrics?.tps || 0.0
        });
      }
    } catch (err) {
      console.error("Command failed:", err);
    }
  };

  const isIgnited = systemStatus === 'running';

  return (
    <div className="war-room-root">
      <AnimatePresence>
        {systemStatus === 'starting' && (
          <DeploymentHUD status={systemStatus} />
        )}
      </AnimatePresence>

      {apiError && (
        <div className="api-error-alert">
          <Zap size={16} />
          <span>{apiError} (Port 8000)</span>
          <button onClick={() => window.location.reload()}>RE-INITIALIZE</button>
        </div>
      )}

      {/* Strategic Header */}
      <header className="strategic-header">
        <div className="logo-section">
          <Shield className="glow-icon" color="var(--accent-cyan)" size={32} />
          <div className="title-block">
            <h1 className="glow-text">GILLSYSTEMS COMMANDER OS</h1>
            <span className="subtitle">STRATEGIC DASHBOARD // v{systemVersion}</span>
          </div>
        </div>

        <div className="system-status">
          <div className="status-item">
            <Activity size={18} color={systemStatus === 'running' ? 'var(--success)' : 'var(--warning)'} />
            <span>{systemStatus === 'running' ? 'CLUSTER ONLINE' : systemStatus === 'starting' ? 'BOOTING PROTOCOLS' : 'OFFLINE'}</span>
          </div>

          {isIgnited && (
            <button className="shutdown-button" onClick={handleShutdown}>
              <Power size={18} /> SHUTDOWN SYSTEM
            </button>
          )}

          <button
            className={`ignite-button ${isIgnited ? 'active' : ''} ${systemStatus === 'starting' ? 'starting' : ''}`}
            onClick={handleIgnite}
            disabled={systemStatus === 'starting'}
          >
            <Power size={18} />
            {isIgnited ? 'ARMED & ACTIVE' : systemStatus === 'starting' ? 'IGNITING...' : 'IGNITE ALL'}
          </button>
        </div>
      </header>

      {/* Main Command Area */}
      <main className="command-grid">
        <section className="nodes-section">
          <div className="section-header">
            <Layout size={20} />
            <h2>INTELLIGENCE NODES</h2>
            {selectedNode && (
              <button 
                className="deselect-btn"
                onClick={() => setSelectedNode(null)}
                style={{ 
                  marginLeft: 'auto', 
                  padding: '4px 10px', 
                  fontSize: '0.7rem',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid var(--border-dim)',
                  borderRadius: '4px',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer'
                }}
              >
                VIEW ALL
              </button>
            )}
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
                    <span>{(node.metrics?.tps || 0).toFixed(1)} TPS // {node.tps_benchmark || 0} MAX</span>
                  </div>
                </div>
                <div className="node-gauge">
                  <div className={`gauge-fill ${node.status}`} style={{ width: `${Math.min(100, ((node.metrics?.tps || 0) / (node.tps_benchmark || 100)) * 100)}%` }}></div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Node Control Panel - Below Nodes */}
          <div className="tab-header">
            <button 
              className={`tab-btn ${activeTab === 'control' ? 'active' : ''}`}
              onClick={() => setActiveTab('control')}
            >
              <Settings size={16} /> NODE CONTROL
            </button>
            <button 
              className={`tab-btn ${activeTab === 'stats' ? 'active' : ''}`}
              onClick={() => setActiveTab('stats')}
            >
              <BarChart3 size={16} /> STATS FOR NERDS
            </button>
          </div>

          <AnimatePresence mode="wait">
            {activeTab === 'control' && selectedNode ? (
              <motion.div
                key={selectedNode.node_id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="control-panel panel-container"
              >
                <div className="panel-header strategic-border">
                  <h3>NODE CONTROL: {selectedNode.name || selectedNode.node_id}</h3>
                  {selectedNode.status === 'online' && (
                    <button className="node-stop-btn" onClick={handleStopNode}>STOP NODE</button>
                  )}
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
                    <label>LOCAL MODELS</label>
                    <div className="model-select-wrapper">
                      <Database size={18} />
                      <select
                        className="strategic-select"
                        value={dials.model_file}
                        onChange={(e) => setDials({ ...dials, model_file: e.target.value })}
                      >
                        {availableModels.length === 0 ? (
                          <option value="">No models found - check model_root_path</option>
                        ) : (
                          <>
                            {availableModels.map(m => (
                              <option key={m} value={m}>{m}</option>
                            ))}
                          </>
                        )}
                      </select>
                      <RefreshCw 
                        size={14} 
                        className="spin-hover" 
                        style={{ cursor: 'pointer' }}
                        onClick={() => {
                          if (selectedNode) {
                            api.listModels(selectedNode.node_id)
                              .then(setAvailableModels)
                              .catch(err => console.error("Failed to refresh models:", err));
                          }
                        }}
                      />
                    </div>
                  </div>

                  <div className="action-footer">
                    <button className="apply-button" onClick={handleSaveDials}>SAVE & RE-IGNITE</button>
                  </div>
                </div>
              </motion.div>
            ) : activeTab === 'control' ? (
              <div className="empty-panel panel-container">
                <Terminal size={48} color="var(--border-dim)" />
                <p>SELECT A NODE TO ACCESS COMMAND DIALS</p>
              </div>
            ) : null}

            {activeTab === 'stats' && (
              <motion.div
                key="stats-tab"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="stats-panel panel-container"
              >
                <div className="panel-header strategic-border">
                  <h3>STATS FOR NERDS</h3>
                  <span className="live-indicator">● LIVE</span>
                </div>
                
                <div className="stats-grid">
                  <div className="stat-card">
                    <span className="stat-label">SYSTEM STATUS</span>
                    <span className="stat-value">{systemStatus.toUpperCase()}</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-label">TOTAL NODES</span>
                    <span className="stat-value">{nodes.length}</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-label">ONLINE NODES</span>
                    <span className="stat-value">{nodes.filter(n => n.status === 'ready' || n.status === 'online').length}</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-label">TOTAL AGENTS</span>
                    <span className="stat-value">{agents.length}</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-label">MESSAGE BUFFER</span>
                    <span className="stat-value">{traffic.length}</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-label">VERSION</span>
                    <span className="stat-value">v{systemVersion}</span>
                  </div>
                </div>

                {selectedNode && (
                  <div className="selected-node-stats">
                    <h4>SELECTED: {selectedNode.name || selectedNode.node_id}</h4>
                    <div className="node-detail-grid">
                      <div className="detail-item">
                        <span className="label">HOST</span>
                        <code>{selectedNode.host || 'N/A'}</code>
                      </div>
                      <div className="detail-item">
                        <span className="label">PORT</span>
                        <code>{selectedNode.port || 'N/A'}</code>
                      </div>
                      <div className="detail-item">
                        <span className="label">STATUS</span>
                        <code className={selectedNode.status}>{selectedNode.status}</code>
                      </div>
                      <div className="detail-item">
                        <span className="label">TPS BENCHMARK</span>
                        <code>{selectedNode.tps_benchmark || 0}</code>
                      </div>
                      <div className="detail-item">
                        <span className="label">CURRENT TPS</span>
                        <code>{(selectedNode.metrics?.tps || 0).toFixed(2)}</code>
                      </div>
                      <div className="detail-item">
                        <span className="label">LOAD %</span>
                        <code>{(selectedNode.metrics?.load || 0).toFixed(1)}%</code>
                      </div>
                    </div>
                  </div>
                )}

                <div className="raw-state">
                  <h4>CLUSTER NODE LIST (RAW)</h4>
                  <pre>{JSON.stringify(nodes, null, 2)}</pre>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </section>

        {/* Right Panel - Chat with The Commander */}
        <section className="control-section">
          <div className="section-header">
            <Radio size={20} />
            <h2>THE COMMANDER</h2>
          </div>
          <CommanderChat data={traffic} onSend={handleCommand} stats={chatStats} />
        </section>
      </main>

      <footer className="strategic-footer">
        <div className="footer-status">
          <Database size={14} />
          <span>ZFS POOL: ONLINE // /gillsystems_zfs_pool/AI_storage</span>
        </div>
        <div className="version-info">
          v{systemVersion} // GILLSYSTEMS STRATEGIC INTEL
        </div>
      </footer>
    </div>
  );
}

export default App;
