export const integration_statusEndpoint = "/integration-status";
export function withCursor(endpoint, cursor) { return cursor ? `${endpoint}?cursor=${encodeURIComponent(cursor)}` : endpoint; }
