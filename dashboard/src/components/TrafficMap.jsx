import React from 'react';
import {
    HiOutlineLocationMarker,
    HiOutlineTruck,
    HiOutlineClock,
    HiOutlineShieldCheck
} from 'react-icons/hi';

/**
 * TrafficMap — Overview tab content.
 * Shows stat cards and an intersection grid with live signal states.
 */
function TrafficMap({ intersections, liveData, systemStatus }) {
    // Derive stats from live data
    const latestDetections = liveData.filter((d) => d.type === 'detection');
    const totalVehiclesNow = latestDetections.length > 0
        ? latestDetections[0]?.data?.total_vehicles || 0
        : 0;

    const stats = [
        {
            icon: <HiOutlineLocationMarker size={22} />,
            iconBg: 'var(--accent-indigo-glow)',
            iconColor: 'var(--accent-indigo)',
            value: systemStatus?.total_intersections || intersections.length || 0,
            label: 'Active Intersections',
            trend: null
        },
        {
            icon: <HiOutlineTruck size={22} />,
            iconBg: 'var(--accent-emerald-glow)',
            iconColor: 'var(--accent-emerald)',
            value: totalVehiclesNow,
            label: 'Vehicles Detected (Live)',
            trend: null
        },
        {
            icon: <HiOutlineClock size={22} />,
            iconBg: 'var(--accent-amber-glow)',
            iconColor: 'var(--accent-amber)',
            value: systemStatus?.total_detections?.toLocaleString() || '0',
            label: 'Total Detections',
            trend: null
        },
        {
            icon: <HiOutlineShieldCheck size={22} />,
            iconBg: 'var(--accent-rose-glow)',
            iconColor: 'var(--accent-rose)',
            value: systemStatus?.total_commands || 0,
            label: 'Signal Commands Sent',
            trend: null
        }
    ];

    // Demo intersections if no real data yet
    const displayIntersections = intersections.length > 0
        ? intersections
        : [
            { intersection_id: 'INT-001', name: 'Main St & 5th Ave', num_lanes: 4, is_active: true },
            { intersection_id: 'INT-002', name: 'Park Rd & Oak Blvd', num_lanes: 3, is_active: true },
            { intersection_id: 'INT-003', name: 'Highway 101 Ramp', num_lanes: 6, is_active: true },
            { intersection_id: 'INT-004', name: 'Downtown Square', num_lanes: 4, is_active: true },
            { intersection_id: 'INT-005', name: 'Riverside & Bridge', num_lanes: 2, is_active: false },
            { intersection_id: 'INT-006', name: 'Tech Park Junction', num_lanes: 4, is_active: true }
        ];

    // Simulate signal states based on intersection index
    const getSignalPhase = (idx) => {
        const phases = ['GREEN', 'RED', 'GREEN', 'YELLOW', 'RED', 'GREEN'];
        return phases[idx % phases.length];
    };

    const getVehicleCount = (idx) => {
        const counts = [12, 8, 23, 5, 0, 15];
        return counts[idx % counts.length];
    };

    return (
        <div>
            {/* Stat Cards */}
            <div className="stats-grid">
                {stats.map((stat, i) => (
                    <div className="card stat-card" key={i}>
                        <div
                            className="stat-icon"
                            style={{ background: stat.iconBg, color: stat.iconColor }}
                        >
                            {stat.icon}
                        </div>
                        <div className="stat-value" style={{ color: stat.iconColor }}>
                            {stat.value}
                        </div>
                        <div className="stat-label">{stat.label}</div>
                    </div>
                ))}
            </div>

            {/* Section Title */}
            <h2 style={{
                fontSize: '1rem',
                fontWeight: 700,
                marginBottom: 'var(--space-lg)',
                color: 'var(--text-primary)'
            }}>
                Intersection Monitor
            </h2>

            {/* Intersection Grid */}
            <div className="intersection-grid">
                {displayIntersections.map((intersection, idx) => {
                    const phase = getSignalPhase(idx);
                    const vehicleCount = getVehicleCount(idx);

                    return (
                        <div className="card intersection-card" key={intersection.intersection_id}>
                            <div className="intersection-header">
                                <div>
                                    <div className="intersection-name">{intersection.name}</div>
                                    <div className="intersection-id">{intersection.intersection_id}</div>
                                </div>
                                <div className="traffic-light">
                                    <div className={`light ${phase === 'RED' ? 'active-red' : ''}`} />
                                    <div className={`light ${phase === 'YELLOW' ? 'active-yellow' : ''}`} />
                                    <div className={`light ${phase === 'GREEN' ? 'active-green' : ''}`} />
                                </div>
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'var(--space-md)' }}>
                                <div>
                                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '2px' }}>
                                        Vehicles
                                    </div>
                                    <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>
                                        {vehicleCount}
                                    </div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '2px' }}>
                                        Lanes
                                    </div>
                                    <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>
                                        {intersection.num_lanes}
                                    </div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '2px' }}>
                                        Status
                                    </div>
                                    <div style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px',
                                        marginTop: '4px'
                                    }}>
                                        <span className={`signal-dot ${intersection.is_active ? 'green' : 'red'}`} />
                                        <span style={{
                                            fontSize: '0.8rem',
                                            fontWeight: 600,
                                            color: intersection.is_active ? 'var(--accent-emerald)' : 'var(--accent-rose)'
                                        }}>
                                            {intersection.is_active ? 'Active' : 'Offline'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Live Feed */}
            {liveData.length > 0 && (
                <div style={{ marginTop: 'var(--space-xl)' }}>
                    <h2 style={{
                        fontSize: '1rem',
                        fontWeight: 700,
                        marginBottom: 'var(--space-lg)',
                        color: 'var(--text-primary)'
                    }}>
                        Live Feed
                    </h2>
                    <div className="card" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                        {liveData.slice(0, 20).map((item, idx) => (
                            <div
                                key={idx}
                                style={{
                                    padding: 'var(--space-sm) 0',
                                    borderBottom: '1px solid var(--border-subtle)',
                                    fontSize: '0.8rem',
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    color: 'var(--text-secondary)'
                                }}
                            >
                                <span style={{ fontFamily: 'monospace', color: 'var(--accent-indigo)' }}>
                                    {item.type}
                                </span>
                                <span>
                                    {item.data?.intersection_id || 'N/A'} — {item.data?.total_vehicles ?? 0} vehicles
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

export default TrafficMap;
