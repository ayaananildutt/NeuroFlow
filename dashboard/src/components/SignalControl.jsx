import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { HiOutlineRefresh } from 'react-icons/hi';

/**
 * SignalControl — Manual signal override panel.
 * Allows operators to manually control traffic light phases per intersection.
 */
function SignalControl({ intersections, onOverride }) {
    const [selectedIntersection, setSelectedIntersection] = useState('');
    const [selectedPhase, setSelectedPhase] = useState('GREEN');
    const [duration, setDuration] = useState(30);
    const [signalHistory, setSignalHistory] = useState([]);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [statusMessage, setStatusMessage] = useState(null);

    const displayIntersections = intersections.length > 0
        ? intersections
        : [
            { intersection_id: 'INT-001', name: 'Main St & 5th Ave' },
            { intersection_id: 'INT-002', name: 'Park Rd & Oak Blvd' },
            { intersection_id: 'INT-003', name: 'Highway 101 Ramp' },
            { intersection_id: 'INT-004', name: 'Downtown Square' },
            { intersection_id: 'INT-005', name: 'Riverside & Bridge' },
            { intersection_id: 'INT-006', name: 'Tech Park Junction' }
        ];

    useEffect(() => {
        if (!selectedIntersection && displayIntersections.length > 0) {
            setSelectedIntersection(displayIntersections[0].intersection_id);
        }
    }, [displayIntersections]);

    useEffect(() => {
        if (selectedIntersection) {
            fetchSignalHistory();
        }
    }, [selectedIntersection]);

    const fetchSignalHistory = async () => {
        try {
            const data = await api.getSignalHistory(selectedIntersection, 10);
            setSignalHistory(data);
        } catch (err) {
            // Demo history
            setSignalHistory([
                { id: 1, phase: 'GREEN', duration_sec: 45, reason: 'High density detected (78%). Dominant type: car.', vehicle_density: 0.78, is_override: false, timestamp: new Date(Date.now() - 120000).toISOString() },
                { id: 2, phase: 'RED', duration_sec: 30, reason: 'Low density (12%). Yielding to cross traffic.', vehicle_density: 0.12, is_override: false, timestamp: new Date(Date.now() - 240000).toISOString() },
                { id: 3, phase: 'GREEN', duration_sec: 60, reason: 'Manual override to GREEN for 60s.', vehicle_density: 0, is_override: true, timestamp: new Date(Date.now() - 360000).toISOString() },
                { id: 4, phase: 'YELLOW', duration_sec: 5, reason: 'Transition phase.', vehicle_density: 0.45, is_override: false, timestamp: new Date(Date.now() - 480000).toISOString() },
                { id: 5, phase: 'RED', duration_sec: 30, reason: 'Low density (23%). Yielding to cross traffic.', vehicle_density: 0.23, is_override: false, timestamp: new Date(Date.now() - 600000).toISOString() }
            ]);
        }
    };

    const handleOverride = async () => {
        setIsSubmitting(true);
        setStatusMessage(null);

        try {
            await api.overrideSignal(selectedIntersection, selectedPhase, duration);
            setStatusMessage({ type: 'success', text: `Signal overridden to ${selectedPhase} for ${duration}s` });
            fetchSignalHistory();
            if (onOverride) onOverride();
        } catch (err) {
            setStatusMessage({ type: 'error', text: 'Override failed. Server may be offline.' });
        } finally {
            setIsSubmitting(false);
        }
    };

    const phases = [
        { value: 'RED', label: 'Red', color: '#ef4444', glow: 'rgba(239, 68, 68, 0.2)' },
        { value: 'YELLOW', label: 'Yellow', color: '#eab308', glow: 'rgba(234, 179, 8, 0.2)' },
        { value: 'GREEN', label: 'Green', color: '#22c55e', glow: 'rgba(34, 197, 94, 0.2)' },
        { value: 'FLASHING_RED', label: 'Flashing Red', color: '#ef4444', glow: 'rgba(239, 68, 68, 0.2)' }
    ];

    return (
        <div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-lg)' }}>
                {/* Override Panel */}
                <div className="card">
                    <div className="card-title">Manual Override</div>

                    {/* Intersection Selector */}
                    <div style={{ marginBottom: 'var(--space-lg)' }}>
                        <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                            Select Intersection
                        </label>
                        <select
                            value={selectedIntersection}
                            onChange={(e) => setSelectedIntersection(e.target.value)}
                            style={{
                                width: '100%',
                                padding: '0.6rem 1rem',
                                borderRadius: 'var(--radius-sm)',
                                border: '1px solid var(--border-default)',
                                background: 'var(--bg-primary)',
                                color: 'var(--text-primary)',
                                fontFamily: 'inherit',
                                fontSize: '0.85rem'
                            }}
                        >
                            {displayIntersections.map((int) => (
                                <option key={int.intersection_id} value={int.intersection_id}>
                                    {int.name} ({int.intersection_id})
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Phase Selector */}
                    <div style={{ marginBottom: 'var(--space-lg)' }}>
                        <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '8px' }}>
                            Signal Phase
                        </label>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
                            {phases.map((phase) => (
                                <button
                                    key={phase.value}
                                    onClick={() => setSelectedPhase(phase.value)}
                                    style={{
                                        padding: '0.6rem',
                                        borderRadius: 'var(--radius-sm)',
                                        border: `2px solid ${selectedPhase === phase.value ? phase.color : 'var(--border-subtle)'}`,
                                        background: selectedPhase === phase.value ? phase.glow : 'transparent',
                                        color: selectedPhase === phase.value ? phase.color : 'var(--text-secondary)',
                                        fontFamily: 'inherit',
                                        fontWeight: 600,
                                        fontSize: '0.85rem',
                                        cursor: 'pointer',
                                        transition: 'all var(--transition-fast)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '8px'
                                    }}
                                >
                                    <span style={{
                                        width: 10,
                                        height: 10,
                                        borderRadius: '50%',
                                        background: phase.color,
                                        display: 'inline-block'
                                    }} />
                                    {phase.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Duration */}
                    <div style={{ marginBottom: 'var(--space-lg)' }}>
                        <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                            Duration: {duration}s
                        </label>
                        <input
                            type="range"
                            min={5}
                            max={120}
                            step={5}
                            value={duration}
                            onChange={(e) => setDuration(parseInt(e.target.value))}
                            style={{ width: '100%', accentColor: 'var(--accent-indigo)' }}
                        />
                        <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            fontSize: '0.7rem',
                            color: 'var(--text-muted)',
                            marginTop: '4px'
                        }}>
                            <span>5s</span>
                            <span>60s</span>
                            <span>120s</span>
                        </div>
                    </div>

                    {/* Submit */}
                    <button
                        className="btn btn-primary"
                        onClick={handleOverride}
                        disabled={isSubmitting}
                        style={{ width: '100%', justifyContent: 'center', padding: '0.7rem' }}
                    >
                        {isSubmitting ? 'Sending Command...' : 'Apply Override'}
                    </button>

                    {/* Status Message */}
                    {statusMessage && (
                        <div style={{
                            marginTop: 'var(--space-md)',
                            padding: 'var(--space-sm) var(--space-md)',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: '0.8rem',
                            fontWeight: 600,
                            background: statusMessage.type === 'success'
                                ? 'var(--accent-emerald-glow)'
                                : 'var(--accent-rose-glow)',
                            color: statusMessage.type === 'success'
                                ? 'var(--accent-emerald)'
                                : 'var(--accent-rose)',
                            border: `1px solid ${statusMessage.type === 'success'
                                ? 'rgba(16,185,129,0.3)'
                                : 'rgba(244,63,94,0.3)'}`
                        }}>
                            {statusMessage.text}
                        </div>
                    )}
                </div>

                {/* Signal History */}
                <div className="card">
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        marginBottom: 'var(--space-md)'
                    }}>
                        <div className="card-title" style={{ marginBottom: 0 }}>Command History</div>
                        <button className="btn" onClick={fetchSignalHistory} style={{ padding: '4px 8px' }}>
                            <HiOutlineRefresh size={16} />
                        </button>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {signalHistory.map((cmd, idx) => (
                            <div
                                key={cmd.id || idx}
                                style={{
                                    padding: 'var(--space-sm) var(--space-md)',
                                    borderRadius: 'var(--radius-sm)',
                                    border: '1px solid var(--border-subtle)',
                                    background: 'rgba(10, 14, 26, 0.5)',
                                    fontSize: '0.8rem'
                                }}
                            >
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'space-between',
                                    marginBottom: '4px'
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <span className={`signal-dot ${cmd.phase?.toLowerCase() === 'green' ? 'green' : cmd.phase?.toLowerCase() === 'yellow' ? 'yellow' : 'red'}`} />
                                        <span style={{ fontWeight: 600 }}>{cmd.phase}</span>
                                        <span style={{ color: 'var(--text-muted)' }}>for {cmd.duration_sec}s</span>
                                        {cmd.is_override && (
                                            <span style={{
                                                fontSize: '0.65rem',
                                                background: 'var(--accent-amber-glow)',
                                                color: 'var(--accent-amber)',
                                                padding: '1px 6px',
                                                borderRadius: '999px',
                                                fontWeight: 700
                                            }}>
                                                OVERRIDE
                                            </span>
                                        )}
                                    </div>
                                    <span style={{
                                        fontSize: '0.7rem',
                                        color: 'var(--text-muted)',
                                        fontFamily: 'monospace'
                                    }}>
                                        {cmd.timestamp ? new Date(cmd.timestamp).toLocaleTimeString() : '—'}
                                    </span>
                                </div>
                                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                                    {cmd.reason}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default SignalControl;
