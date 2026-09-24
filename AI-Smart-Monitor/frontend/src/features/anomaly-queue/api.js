export const anomaly_queueEndpoint = "/anomaly-queue";
export function withCursor(endpoint, cursor) { return cursor ? `${endpoint}?cursor=${encodeURIComponent(cursor)}` : endpoint; }
