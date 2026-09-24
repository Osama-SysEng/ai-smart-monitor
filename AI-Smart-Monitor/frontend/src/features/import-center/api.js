export const import_centerEndpoint = "/import-center";
export function withCursor(endpoint, cursor) { return cursor ? `${endpoint}?cursor=${encodeURIComponent(cursor)}` : endpoint; }
