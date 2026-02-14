import axios from 'axios';

/**
 * NeuroFlow API Client
 * Handles all HTTP and WebSocket communication with the Traffic Controller Server.
 */

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_BASE = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/api/ws/live';

const client = axios.create({
    baseURL: `${API_BASE}/api`,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Response interceptor for error handling
client.interceptors.response.use(
    (response) => response.data,
    (error) => {
        console.error('API Error:', error.response?.data || error.message);
        throw error;
    }
);

export const api = {
    /**
     * Get system health status.
     */
    getHealth: () => client.get('/health'),

    /**
     * Get overall system status.
     */
    getSystemStatus: () => client.get('/status'),

    /**
     * List all active intersections.
     */
    getIntersections: () => client.get('/intersections'),

    /**
     * Get details for a specific intersection.
     * @param {string} intersectionId
     */
    getIntersection: (intersectionId) =>
        client.get(`/intersections/${intersectionId}`),

    /**
     * Fetch recent detections, optionally filtered by intersection.
     * @param {string|null} intersectionId
     * @param {number} limit
     */
    getDetections: (intersectionId = null, limit = 50) => {
        const params = { limit };
        if (intersectionId) params.intersection_id = intersectionId;
        return client.get('/detections', { params });
    },

    /**
     * Get aggregated metrics for an intersection over a time period.
     * @param {string} intersectionId
     * @param {number} periodMinutes
     */
    getMetrics: (intersectionId, periodMinutes = 60) =>
        client.get(`/metrics/${intersectionId}`, {
            params: { period_minutes: periodMinutes }
        }),

    /**
     * Get signal command history for an intersection.
     * @param {string} intersectionId
     * @param {number} limit
     */
    getSignalHistory: (intersectionId, limit = 20) =>
        client.get(`/signals/${intersectionId}/history`, {
            params: { limit }
        }),

    /**
     * Send a manual signal override command.
     * @param {string} intersectionId
     * @param {string} phase - RED, YELLOW, GREEN, FLASHING_RED
     * @param {number} durationSec
     */
    overrideSignal: (intersectionId, phase, durationSec) =>
        client.post(`/signals/${intersectionId}/override`, {
            phase,
            duration_sec: durationSec
        })
};

/**
 * Connect to the WebSocket for live updates.
 * @param {function} onMessage - Callback invoked with each message data object.
 * @param {function} onClose - Callback invoked when connection closes.
 * @returns {WebSocket} The WebSocket instance.
 */
export function connectWebSocket(onMessage, onClose) {
    let ws;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 10;
    const baseReconnectDelay = 1000;

    function connect() {
        try {
            ws = new WebSocket(WS_BASE);

            ws.onopen = () => {
                console.log('[WS] Connected to live feed');
                reconnectAttempts = 0;
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    onMessage(data);
                } catch (err) {
                    console.error('[WS] Failed to parse message:', err);
                }
            };

            ws.onclose = (event) => {
                console.log('[WS] Connection closed:', event.code, event.reason);
                if (onClose) onClose();

                // Auto-reconnect with exponential backoff
                if (reconnectAttempts < maxReconnectAttempts) {
                    const delay = baseReconnectDelay * Math.pow(2, reconnectAttempts);
                    reconnectAttempts++;
                    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${reconnectAttempts})...`);
                    setTimeout(connect, delay);
                } else {
                    console.error('[WS] Max reconnection attempts reached.');
                }
            };

            ws.onerror = (error) => {
                console.error('[WS] Error:', error);
            };
        } catch (err) {
            console.error('[WS] Failed to create WebSocket:', err);
        }
    }

    connect();
    return ws;
}

export default api;
