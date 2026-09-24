export function byStatus(items, status) { return status === "ALL" ? items : items.filter(item => item.status === status); }
export function byQuery(items, query, keys = ["id", "status"]) { const needle = query.trim().toLowerCase(); return !needle ? items : items.filter(item => keys.some(key => String(item[key] ?? "").toLowerCase().includes(needle))); }
