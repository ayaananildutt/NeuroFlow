import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import TrafficMap from './components/TrafficMap';
import MetricsPanel from './components/MetricsPanel';
import SignalControl from './components/SignalControl';
import { api, connectWebSocket } from './services/api';
import {
    HiOutlineViewGrid,
    HiOutlineChartBar,
    HiOutlineCog,
    HiOutlineStatusOnline,
    HiOutlineAdjustments
} from 'react-icons/hi';

function App() {
    const [activeTab, setActiveTab] = useState('overview');
    const [systemStatus, setSystemStatus] = useState(null);
    const [intersections, setIntersections] = useState([]);
    const [liveData, setLiveData] = useState([]);
    const [wsConnected, setWsConnected] = useState(false);

    useEffect(() => {
        // Fetch initial data
        fetchSystemStatus();
        fetchIntersections();

        // Connect WebSocket for live updates
        const ws = connectWebSocket(
            (data) => {
                setLiveData((prev) => [data, ...prev].slice(0, 100));
                setWsConnected(true);
            },
            () => setWsConnected(false)
        );

        // Refresh system status every 30 seconds
        const interval = setInterval(fetchSystemStatus, 30000);

        return () => {
            clearInterval(interval);
            if (ws) ws.close();
        };
    }, []);

    const fetchSystemStatus = async () => {
        try {
            const data = await api.getSystemStatus();
            setSystemStatus(data);
        } catch (err) {
            console.error('Failed to fetch system status:', err);
        }
    };

    const fetchIntersections = async () => {
        try {
            const data = await api.getIntersections();
            setIntersections(data);
        } catch (err) {
            console.error('Failed to fetch intersections:', err);
        }
    };

    const navItems = [
        { id: 'overview', label: 'Overview', icon: <HiOutlineViewGrid size={20} /> },
        { id: 'metrics', label: 'Analytics', icon: <HiOutlineChartBar size={20} /> },
        { id: 'control', label: 'Signal Control', icon: <HiOutlineAdjustments size={20} /> },
    ];

    return (
        <div className="app-layout">
            {/* Sidebar */}
            <aside className="sidebar">
                <div style={{ marginBottom: '2rem' }}>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.75rem',
                        marginBottom: '0.25rem'
                    }}>
                        <span style={{ fontSize: '1.5rem' }}>🚦</span>
                        <span style={{
                            fontSize: '1.1rem',
                            fontWeight: 800,
                            background: 'linear-gradient(135deg, #c7d2fe, #818cf8)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent'
                        }}>
                            NeuroFlow
                        </span>
                    </div>
                    <span style={{
                        fontSize: '0.7rem',
                        color: 'var(--text-muted)',
                        letterSpacing: '0.08em',
                        textTransform: 'uppercase'
                    }}>
                        Autonomous Traffic Control
                    </span>
                </div>

                <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {navItems.map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setActiveTab(item.id)}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.75rem',
                                padding: '0.65rem 0.9rem',
                                border: 'none',
                                borderRadius: 'var(--radius-sm)',
                                background: activeTab === item.id
                                    ? 'var(--accent-indigo-glow)'
                                    : 'transparent',
                                color: activeTab === item.id
                                    ? 'var(--accent-indigo)'
                                    : 'var(--text-secondary)',
                                fontSize: '0.85rem',
                                fontWeight: 500,
                                fontFamily: 'inherit',
                                cursor: 'pointer',
                                transition: 'all var(--transition-fast)',
                                textAlign: 'left',
                                borderLeft: activeTab === item.id
                                    ? '3px solid var(--accent-indigo)'
                                    : '3px solid transparent'
                            }}
                        >
                            {item.icon}
                            {item.label}
                        </button>
                    ))}
                </nav>

                {/* System Info */}
                <div style={{
                    marginTop: 'auto',
                    padding: 'var(--space-md)',
                    background: 'rgba(99, 102, 241, 0.05)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)'
                }}>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        marginBottom: '0.5rem'
                    }}>
                        <HiOutlineStatusOnline
                            size={16}
                            color={wsConnected ? 'var(--accent-emerald)' : 'var(--accent-rose)'}
                        />
                        <span style={{
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            color: wsConnected ? 'var(--accent-emerald)' : 'var(--accent-rose)'
                        }}>
                            {wsConnected ? 'Live Connected' : 'Disconnected'}
                        </span>
                    </div>
                    {systemStatus && (
                        <>
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '2px' }}>
                                Intersections: {systemStatus.total_intersections}
                            </div>
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '2px' }}>
                                Total Detections: {systemStatus.total_detections?.toLocaleString()}
                            </div>
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                                Uptime: {Math.floor((systemStatus.uptime_sec || 0) / 3600)}h {Math.floor(((systemStatus.uptime_sec || 0) % 3600) / 60)}m
                            </div>
                        </>
                    )}
                </div>
            </aside>

            {/* Header */}
            <Header
                activeTab={activeTab}
                wsConnected={wsConnected}
                systemStatus={systemStatus}
            />

            {/* Main Content */}
            <main className="main-content">
                {activeTab === 'overview' && (
                    <TrafficMap
                        intersections={intersections}
                        liveData={liveData}
                        systemStatus={systemStatus}
                    />
                )}
                {activeTab === 'metrics' && (
                    <MetricsPanel
                        intersections={intersections}
                    />
                )}
                {activeTab === 'control' && (
                    <SignalControl
                        intersections={intersections}
                        onOverride={fetchIntersections}
                    />
                )}
            </main>
        </div>
    );
}

export default App;
