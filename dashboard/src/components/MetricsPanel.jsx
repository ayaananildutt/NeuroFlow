import React, { useState, useEffect } from 'react';
import {
    LineChart, Line, BarChart, Bar, AreaChart, Area,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { api } from '../services/api';

/**
 * MetricsPanel — Analytics tab.
 * Displays traffic charts for vehicle counts, congestion trends, and inference performance.
 */
function MetricsPanel({ intersections }) {
    const [selectedIntersection, setSelectedIntersection] = useState('INT-001');
    const [detections, setDetections] = useState([]);
    const [metrics, setMetrics] = useState(null);

    useEffect(() => {
        fetchData();
    }, [selectedIntersection]);

    const fetchData = async () => {
        try {
            const [detectionsData, metricsData] = await Promise.all([
                api.getDetections(selectedIntersection, 50),
                api.getMetrics(selectedIntersection, 60)
            ]);
            setDetections(detectionsData);
            setMetrics(metricsData);
        } catch (err) {
            console.error('Failed to fetch analytics data:', err);
            // Use demo data when API is unavailable
            setDetections(generateDemoDetections());
            setMetrics(generateDemoMetrics());
        }
    };

    // Generate demo data for display when the server is offline
    const generateDemoDetections = () => {
        const data = [];
        const now = Date.now();
        for (let i = 49; i >= 0; i--) {
            const base = Math.sin(i * 0.3) * 5 + 10;
            data.push({
                timestamp: new Date(now - i * 30000).toLocaleTimeString(),
                total_vehicles: Math.max(0, Math.round(base + Math.random() * 4)),
                vehicle_counts: {
                    car: Math.round(base * 0.6),
                    truck: Math.round(base * 0.15),
                    bus: Math.round(base * 0.1),
                    motorcycle: Math.round(base * 0.15)
                },
                inference_time_ms: 15 + Math.random() * 10
            });
        }
        return data;
    };

    const generateDemoMetrics = () => ({
        intersection_id: selectedIntersection,
        period_minutes: 60,
        avg_vehicle_count: 11.3,
        max_vehicle_count: 23,
        total_detections: 842,
        avg_inference_ms: 18.7
    });

    // Format detection data for charts
    const chartData = detections.map((d, i) => ({
        time: d.timestamp
            ? (typeof d.timestamp === 'string' && d.timestamp.includes(':')
                ? d.timestamp
                : new Date(d.timestamp).toLocaleTimeString())
            : `T${i}`,
        vehicles: d.total_vehicles || 0,
        cars: d.vehicle_counts?.car || 0,
        trucks: d.vehicle_counts?.truck || 0,
        buses: d.vehicle_counts?.bus || 0,
        motorcycles: d.vehicle_counts?.motorcycle || 0,
        inference: d.inference_time_ms ? parseFloat(d.inference_time_ms.toFixed(1)) : 0
    }));

    const displayIntersections = intersections.length > 0
        ? intersections
        : [
            { intersection_id: 'INT-001', name: 'Main St & 5th Ave' },
            { intersection_id: 'INT-002', name: 'Park Rd & Oak Blvd' },
            { intersection_id: 'INT-003', name: 'Highway 101 Ramp' }
        ];

    const tooltipStyle = {
        backgroundColor: '#0f1629',
        border: '1px solid rgba(99, 102, 241, 0.2)',
        borderRadius: '8px',
        fontSize: '0.75rem'
    };

    const currentMetrics = metrics || generateDemoMetrics();

    return (
        <div>
            {/* Intersection Selector */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-md)',
                marginBottom: 'var(--space-xl)'
            }}>
                <label style={{
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    color: 'var(--text-secondary)'
                }}>
                    Intersection:
                </label>
                <select
                    value={selectedIntersection}
                    onChange={(e) => setSelectedIntersection(e.target.value)}
                    style={{
                        padding: '0.5rem 1rem',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--border-default)',
                        background: 'var(--bg-secondary)',
                        color: 'var(--text-primary)',
                        fontFamily: 'inherit',
                        fontSize: '0.85rem',
                        cursor: 'pointer'
                    }}
                >
                    {displayIntersections.map((int) => (
                        <option key={int.intersection_id} value={int.intersection_id}>
                            {int.name || int.intersection_id}
                        </option>
                    ))}
                </select>
            </div>

            {/* Metrics Summary Cards */}
            <div className="stats-grid" style={{ marginBottom: 'var(--space-xl)' }}>
                {[
                    { label: 'Avg Vehicles / Frame', value: currentMetrics.avg_vehicle_count, color: 'var(--accent-indigo)' },
                    { label: 'Max Vehicles', value: currentMetrics.max_vehicle_count, color: 'var(--accent-amber)' },
                    { label: 'Total Detections', value: currentMetrics.total_detections, color: 'var(--accent-emerald)' },
                    { label: 'Avg Inference (ms)', value: currentMetrics.avg_inference_ms, color: 'var(--accent-rose)' }
                ].map((m, i) => (
                    <div className="card stat-card" key={i}>
                        <div className="stat-label">{m.label}</div>
                        <div className="stat-value" style={{ color: m.color, fontSize: '1.5rem' }}>
                            {typeof m.value === 'number' ? m.value.toLocaleString(undefined, { maximumFractionDigits: 1 }) : m.value}
                        </div>
                    </div>
                ))}
            </div>

            {/* Charts */}
            <div className="charts-grid">
                {/* Vehicle Count Over Time */}
                <div className="card">
                    <div className="card-title">Vehicle Count — Real-Time</div>
                    <ResponsiveContainer width="100%" height={280}>
                        <AreaChart data={chartData}>
                            <defs>
                                <linearGradient id="vehicleGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#6366f1" stopOpacity={0.3} />
                                    <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                            <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#64748b' }} interval="preserveStartEnd" />
                            <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
                            <Tooltip contentStyle={tooltipStyle} />
                            <Area
                                type="monotone"
                                dataKey="vehicles"
                                stroke="#6366f1"
                                fill="url(#vehicleGradient)"
                                strokeWidth={2}
                                name="Total Vehicles"
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>

                {/* Vehicle Type Breakdown */}
                <div className="card">
                    <div className="card-title">Vehicle Type Breakdown</div>
                    <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={chartData.slice(-15)}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                            <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#64748b' }} />
                            <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
                            <Tooltip contentStyle={tooltipStyle} />
                            <Legend wrapperStyle={{ fontSize: '0.75rem' }} />
                            <Bar dataKey="cars" stackId="a" fill="#6366f1" name="Cars" radius={[0, 0, 0, 0]} />
                            <Bar dataKey="trucks" stackId="a" fill="#f59e0b" name="Trucks" />
                            <Bar dataKey="buses" stackId="a" fill="#10b981" name="Buses" />
                            <Bar dataKey="motorcycles" stackId="a" fill="#f43f5e" name="Motorcycles" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Inference Time */}
                <div className="card">
                    <div className="card-title">YOLOv8 Inference Latency (ms)</div>
                    <ResponsiveContainer width="100%" height={280}>
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                            <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#64748b' }} interval="preserveStartEnd" />
                            <YAxis tick={{ fontSize: 10, fill: '#64748b' }} domain={[0, 'auto']} />
                            <Tooltip contentStyle={tooltipStyle} />
                            <Line
                                type="monotone"
                                dataKey="inference"
                                stroke="#10b981"
                                strokeWidth={2}
                                dot={false}
                                name="Inference (ms)"
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
}

export default MetricsPanel;
