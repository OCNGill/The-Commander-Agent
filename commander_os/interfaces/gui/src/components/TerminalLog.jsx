import React from 'react';
import { Terminal } from 'lucide-react';
import { motion } from 'framer-motion';

const TerminalLog = ({ data = [] }) => {
  return (
    <div className="terminal-panel panel-container">
      <div className="panel-header strategic-border">
        <div className="flex items-center gap-2">
          <Terminal size={18} />
          <h3>STRATEGIC INTELLIGENCE STREAM</h3>
        </div>
      </div>
      <div className="terminal-content">
        {data.map((log, i) => {
          const ts = new Date(log.timestamp * 1000).toLocaleTimeString();
          return (
            <motion.div
              key={log.id || i}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              className="log-entry"
            >
              <span className="log-ts">[{ts}]</span>
              <span className="log-sender">{log.sender}</span>
              <span className="log-arrow">{"->"}</span>
              <span className="log-role">{log.role}:</span>
              <span className="log-msg">{log.content}</span>
            </motion.div>
          );
        })}
        <div className="cursor-blink">_</div>
      </div>

      <style jsx>{`
        .terminal-panel {
          flex: 1;
          display: flex;
          flex-direction: column;
          margin-top: 1.5rem;
          min-height: 200px;
        }
        .terminal-content {
          padding: 1.25rem;
          font-family: 'JetBrains Mono', 'Fira Code', monospace;
          font-size: 0.8rem;
          overflow-y: auto;
          flex: 1;
          background: rgba(0, 0, 0, 0.4);
        }
        .log-entry {
          display: flex;
          gap: 0.75rem;
          margin-bottom: 0.35rem;
          line-height: 1.4;
        }
        .log-ts { color: var(--text-secondary); }
        .log-sender { color: var(--success); font-weight: 700; }
        .log-role { color: var(--accent-cyan); }
        .log-msg { color: var(--text-primary); }
        .log-arrow { color: var(--border-dim); }
        .cursor-blink {
          display: inline-block;
          color: var(--accent-cyan);
          animation: blink 1s infinite steps(2);
        }
        @keyframes blink { to { visibility: hidden; } }
      `}</style>
    </div>
  );
};

export default TerminalLog;
