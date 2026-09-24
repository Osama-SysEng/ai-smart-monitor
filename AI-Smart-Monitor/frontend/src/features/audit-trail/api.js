export const audit_trailEndpoint = "/audit-trail";
export function withCursor(endpoint, cursor) { return cursor ? `${endpoint}?cursor=${encodeURIComponent(cursor)}` : endpoint; }
