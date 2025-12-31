import React, { useState, useEffect, useRef } from 'react';
import { Send, MessageSquare } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const CommanderChat = ({ data = [], onSend, stats = {} }) => {
    const [input, setInput] = useState('');
    const scrollRef = useRef(null);

    // Auto-scroll
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [data]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (input.trim()) {
            onSend(input);
            setInput('');
        }
    };

    return (
        <div className="chat-interface panel-container" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>

            {/* Header */}
            <div className="panel-header strategic-border" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <MessageSquare size={18} color="var(--accent-cyan)" />
                <h3 style={{ margin: 0, color: 'var(--text-primary)' }}>THE COMMANDER</h3>
                <div style={{ flex: 1 }} />
                <div className="status-indicator live" />
            </div>

            {/* Message Stream */}
            <div
                className="chat-content"
                ref={scrollRef}
                style={{
                    flex: 1,
                    overflowY: 'auto',
                    padding: '20px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px',
                    background: 'rgba(0,0,0,0.2)'
                }}
            >
                <AnimatePresence initial={false}>
                    {data.map((msg) => {
                        const isUser = msg.sender === 'THE_COMMANDER' || msg.role === 'user';
                        const isSystem = msg.sender === 'System';

                        return (
                            <motion.div
                                key={msg.id || Math.random()}
                                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                style={{
                                    alignSelf: isUser ? 'flex-end' : 'flex-start',
                                    maxWidth: '80%',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: isUser ? 'flex-end' : 'flex-start'
                                }}
                            >
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    marginBottom: '4px',
                                    fontSize: '10px',
                                    color: 'var(--text-secondary)'
                                }}>
                                    <span>{msg.sender?.toUpperCase()}</span>
                                    <span>{new Date(msg.timestamp * 1000).toLocaleTimeString()}</span>
                                </div>

                                <div style={{
                                    background: isUser ? 'rgba(0, 255, 242, 0.1)' : 'rgba(20, 20, 30, 0.8)',
                                    border: isUser ? '1px solid var(--accent-cyan)' : '1px solid var(--border-dim)',
                                    borderRadius: isUser ? '12px 12px 0 12px' : '12px 12px 12px 0',
                                    padding: '12px 16px',
                                    color: isUser ? 'var(--accent-cyan)' : 'var(--text-primary)',
                                    boxShadow: isUser ? '0 0 10px rgba(0, 255, 242, 0.1)' : 'none',
                                    whiteSpace: 'pre-wrap',
                                    fontFamily: isSystem ? 'monospace' : 'inherit'
                                }}>
                                    {msg.content}
                                </div>
                            </motion.div>
                        );
                    })}
                </AnimatePresence>
            </div>

            {/* Input Area */}
            <form
                onSubmit={handleSubmit}
                style={{
                    padding: '15px',
                    borderTop: '1px solid var(--border-dim)',
                    background: 'var(--bg-panel)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px'
                }}
            >
                {/* Stats Bar - Like llama.cpp server */}
                <div style={{
                    display: 'flex',
                    gap: '15px',
                    fontSize: '10px',
                    color: 'var(--text-secondary)',
                    fontFamily: 'monospace',
                    borderBottom: '1px solid var(--border-dim)',
                    paddingBottom: '8px'
                }}>
                    <span>Node: <strong style={{ color: 'var(--accent-cyan)' }}>{stats.node || 'None'}</strong></span>
                    <span>Model: <strong>{stats.model || 'N/A'}</strong></span>
                    <span>Context: <strong>{stats.context || '0/0'}</strong></span>
                    <span>Output: <strong>{stats.output || 0}</strong></span>
                    <span>Speed: <strong style={{ color: 'var(--success)' }}>{(stats.toksPerSec || 0).toFixed(2)} t/s</strong></span>
                </div>

                {/* Input Field */}
                <div style={{ display: 'flex', gap: '10px' }}>
                <div style={{ position: 'relative', flex: 1 }}>
                    <span style={{
                        position: 'absolute',
                        left: '12px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        color: 'var(--accent-cyan)'
                    }}>&gt;</span>
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Enter orders, Commander..."
                        className="strategic-input"
                        style={{
                            width: '100%',
                            padding: '12px 12px 12px 30px',
                            background: 'rgba(0, 0, 0, 0.3)',
                            border: '1px solid var(--border-dim)',
                            borderRadius: '4px',
                            color: 'var(--text-primary)',
                            fontFamily: 'monospace',
                            outline: 'none'
                        }}
                    />
                </div>
                <button
                    type="submit"
                    className="btn-primary"
                    style={{ padding: '0 20px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                >
                    <Send size={18} />
                </button>
                </div>
            </form>
        </div>
    );
};

export default CommanderChat;
