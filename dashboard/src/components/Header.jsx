import React from 'react';
import { HiOutlineBell, HiOutlineCog } from 'react-icons/hi';

/**
 * Header component — displays current tab name, connection status, and actions.
 */
function Header({ activeTab, wsConnected, systemStatus }) {
    const tabTitles = {
        overview: 'Traffic Overview',
        metrics: 'Analytics & Metrics',
        control: 'Signal Control Panel'
    };

    return (
        <header className="header">
            <div>
                <h1 style={{
                    fontSize: '1.1rem',
                    fontWeight: 700,
                    color: 'var(--text-primary)'
                }}>
                    {tabTitles[activeTab] || 'Dashboard'}
                </h1>
                <p style={{
                    fontSize: '0.75rem',
                    color: 'var(--text-muted)',
                    marginTop: '2px'
                }}>
                    Real-time autonomous traffic monitoring
                </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                {/* Live indicator */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.35rem 0.75rem',
                    borderRadius: '999px',
                    background: wsConnected
                        ? 'var(--accent-emerald-glow)'
                        : 'var(--accent-rose-glow)',
                    border: `1px solid ${wsConnected ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`
                }}>
                    <span
                        className={wsConnected ? 'animate-pulse' : ''}
                        style={{
                            width: 8,
                            height: 8,
                            borderRadius: '50%',
                            background: wsConnected ? 'var(--accent-emerald)' : 'var(--accent-rose)',
                            display: 'inline-block'
                        }}
                    />
                    <span style={{
                        fontSize: '0.7rem',
                        fontWeight: 600,
                        color: wsConnected ? 'var(--accent-emerald)' : 'var(--accent-rose)'
                    }}>
                        {wsConnected ? 'LIVE' : 'OFFLINE'}
                    </span>
                </div>

                {/* Notification button */}
                <button className="btn" style={{ padding: '0.4rem' }}>
                    <HiOutlineBell size={18} />
                </button>

                {/* Settings button */}
                <button className="btn" style={{ padding: '0.4rem' }}>
                    <HiOutlineCog size={18} />
                </button>
            </div>
        </header>
    );
}

export default Header;
