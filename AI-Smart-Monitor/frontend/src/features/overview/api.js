export const overviewEndpoint = "/overview";
export function withCursor(endpoint, cursor) { return cursor ? `${endpoint}?cursor=${encodeURIComponent(cursor)}` : endpoint; }
