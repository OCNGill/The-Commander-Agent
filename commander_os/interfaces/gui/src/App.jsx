import React, { useState, useEffect } from 'react';
import { Shield, Activity, Database, Cpu, Layout, Power, RefreshCw, Terminal } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import TerminalLog from './components/TerminalLog';
import './App.css';

// Mock Data representative of Gillsystems Topology
const MOCK_NODES = [
  { id: 'node-main', name: 'Gillsystems-Main', hardware: '7900XTX', status: 'ready', tps: 130, model: 'Qwen3-Coder-25B', ctx: 131072, ngl: 999 },
  { id: 'node-htpc', name: 'Gillsystems-HTPC', hardware: '7600', status: 'ready', tps: 60, model: 'Granite-4.0-h-tiny', ctx: 114688, ngl: 40 },
  { id: 'node-steamdeck', name: 'Steam Deck Node', hardware: 'Custom APU', status: 'ready', tps: 30, model: 'Granite-4.0-h-tiny', ctx: 21844, ngl: 32 },
  { id: 'node-laptop', name: 'Laptop Node', hardware: 'Integrated', status: 'offline', tps: 9, model: 'Granite-4.0-h-tiny', ctx: 21844, ngl: 999 },
];

function App() {
  const [nodes, setNodes] = useState(MOCK_NODES);
  const [selectedNode, setSelectedNode] = useState(null);
  const [isIgnited, setIsIgnited] = useState(false);

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
            onClick={() => setIsIgnited(!isIgnited)}
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
                key={node.id}
                className={`node-card ${selectedNode?.id === node.id ? 'active' : ''}`}
                whileHover={{ scale: 1.02 }}
                onClick={() => setSelectedNode(node)}
              >
                <div className="node-info">
                  <div className="node-top">
                    <span className="node-name">{node.name}</span>
                    <span className={`status-badge ${node.status}`}>{node.status}</span>
                  </div>
                  <div className="node-hardware">
                    <Cpu size={14} />
                    <span>{node.hardware} // {node.tps} t/s</span>
                  </div>
                </div>
                <div className="node-gauge">
                  <div className={`gauge-fill ${node.status}`} style={{ width: `${(node.tps / 130) * 100}%` }}></div>
                </div>
              </motion.div>
            ))}
          </div>

          <TerminalLog />
        </section>

        <section className="control-section">
          <AnimatePresence mode="wait">
            {selectedNode ? (
              <motion.div
                key={selectedNode.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="control-panel panel-container"
              >
                <div className="panel-header strategic-border">
                  <h3>NODE CONTROL: {selectedNode.name}</h3>
                </div>

                <div className="control-groups">
                  <div className="control-group">
                    <label>HARDWARE ENGINE DIALS</label>
                    <div className="input-grid">
                      <div className="input-box">
                        <span>CONTEXT SIZE</span>
                        <input type="number" defaultValue={selectedNode.ctx} />
                      </div>
                      <div className="input-box">
                        <span>GPU LAYERS (NGL)</span>
                        <input type="number" defaultValue={selectedNode.ngl} />
                      </div>
                    </div>
                  </div>

                  <div className="control-group">
                    <label>MODEL ARMORY</label>
                    <div className="model-selector">
                      <Database size={18} />
                      <span>{selectedNode.model}.gguf</span>
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
