import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Search, Filter, Trash2, ChevronDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const TerminalLog = ({ data = [] }) => {
  const [filter, setFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const scrollRef = useRef(null);

  // Auto-scroll to bottom on new logs
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [data]);

  const roles = [...new Set(data.map(log => log.role))];
  const senders = [...new Set(data.map(log => log.sender))];

  const filteredData = data.filter(log => {
    const matchesFilter = filter === '' || log.sender === filter || log.role === filter;
    const matchesSearch = searchTerm === '' ||
      log.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.sender.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="terminal-panel panel-container">
      <div className="panel-header strategic-border log-header">
        <div className="header-left">
          <Terminal size={18} color="var(--accent-cyan)" />
          <h3>INTELLIGENCE LOG</h3>
        </div>

        <div className="header-actions">
          <div className="search-box">
            <Search size={14} color="var(--text-secondary)" />
            <input
              type="text"
              placeholder="SEARCH MEMORY..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <div className="filter-dropdown">
            <button className="icon-btn" onClick={() => setIsFilterOpen(!isFilterOpen)}>
              <Filter size={16} color={filter ? 'var(--accent-cyan)' : 'var(--text-secondary)'} />
            </button>
            <AnimatePresence>
              {isFilterOpen && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="dropdown-menu"
                >
                  <div className="menu-item" onClick={() => { setFilter(''); setIsFilterOpen(false); }}>ALL TRAFFIC</div>
                  <div className="menu-divider">ROLES</div>
                  {roles.map(r => (
                    <div key={r} className="menu-item" onClick={() => { setFilter(r); setIsFilterOpen(false); }}>{r.toUpperCase()}</div>
                  ))}
                  <div className="menu-divider">SENDERS</div>
                  {senders.map(s => (
                    <div key={s} className="menu-item" onClick={() => { setFilter(s); setIsFilterOpen(false); }}>{s.toUpperCase()}</div>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      <div className="terminal-content" ref={scrollRef}>
        <AnimatePresence initial={false}>
          {filteredData.map((log) => {
            const ts = new Date(log.timestamp * 1000).toLocaleTimeString();
            return (
              <motion.div
                key={log.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className={`log-entry ${log.role?.toLowerCase()}`}
              >
                <span className="log-ts">[{ts}]</span>
                <span className="log-sender">{log.sender}</span>
                <span className="log-role">:: {log.role}</span>
                <span className="log-msg">{log.content}</span>
              </motion.div>
            );
          })}
        </AnimatePresence>
        <div className="cursor-blink">_</div>
      </div>
    </div>
  );
};

export default TerminalLog;
