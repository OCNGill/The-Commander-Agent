import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Rocket, CheckCircle2, CircleDashed, ShieldAlert } from 'lucide-react';

const DeploymentHUD = ({ status }) => {
    const steps = [
        { id: 'engine', label: 'IGNITING HARDWARE ENGINE', status: 'pending' },
        { id: 'relay', label: 'ESTABLISHING RELAY FABRIC', status: 'pending' },
        { id: 'nodes', label: 'SYNCHRONIZING CLUSTER NODES', status: 'pending' },
        { id: 'agents', label: 'DEPLOYING INTELLIGENCE AGENTS', status: 'pending' },
    ];

    // Logic to determine step status based on systemStatus
    // For now, simpler visual progression
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="deployment-hud-overlay"
        >
            <motion.div
                initial={{ scale: 0.9, y: 20 }}
                animate={{ scale: 1, y: 0 }}
                className="hud-card panel-container strategic-border"
            >
                <div className="hud-header">
                    <Rocket className="pulse-icon" color="var(--accent-cyan)" size={32} />
                    <h2>CLUSTER IGNITION SEQUENCE</h2>
                </div>

                <div className="hud-steps">
                    {steps.map((step, index) => (
                        <div key={step.id} className="hud-step">
                            <div className="step-icon">
                                <CircleDashed className="spin-icon" size={18} color="var(--text-secondary)" />
                            </div>
                            <span className="step-label">{step.label}</span>
                        </div>
                    ))}
                </div>

                <div className="hud-footer">
                    <div className="progress-bar">
                        <motion.div
                            className="progress-fill"
                            initial={{ width: '0%' }}
                            animate={{ width: '100%' }}
                            transition={{ duration: 5, ease: "linear" }}
                        />
                    </div>
                    <span className="hud-status-text">PROTOCOLS ENGAGED...</span>
                </div>
            </motion.div>

            <style jsx>{`
        .deployment-hud-overlay {
          position: fixed;
          inset: 0;
          background: rgba(5, 7, 10, 0.9);
          backdrop-filter: blur(8px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }
        .hud-card {
          width: 450px;
          padding: 2rem;
          background: var(--bg-panel);
        }
        .hud-header {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1rem;
          margin-bottom: 2rem;
        }
        .hud-header h2 {
          font-size: 1.25rem;
          letter-spacing: 0.2em;
          color: var(--accent-cyan);
          text-shadow: 0 0 10px rgba(0, 242, 255, 0.3);
        }
        .hud-steps {
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
          margin-bottom: 2rem;
        }
        .hud-step {
          display: flex;
          align-items: center;
          gap: 1rem;
        }
        .step-label {
          font-size: 0.8rem;
          font-weight: 700;
          letter-spacing: 0.1em;
          color: var(--text-secondary);
        }
        .progress-bar {
          height: 4px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 2px;
          overflow: hidden;
          margin-bottom: 0.75rem;
        }
        .progress-fill {
          height: 100%;
          background: var(--accent-cyan);
          box-shadow: 0 0 15px rgba(0, 242, 255, 0.5);
        }
        .hud-status-text {
          font-size: 0.7rem;
          color: var(--accent-cyan);
          font-weight: 800;
          letter-spacing: 0.1em;
          text-align: center;
          display: block;
        }
        .pulse-icon {
          animation: pulse 2s infinite;
        }
        .spin-icon {
          animation: spin 2s infinite linear;
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.7; transform: scale(1.1); }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
        </motion.div>
    );
};

export default DeploymentHUD;
