# ERP Delivery Boundary

Only approved records enter the outbox. Each delivery carries a stable idempotency key and correlation ID. Timeouts, non-success responses, and validation failures are classified before retry; irreversible actions require an operator-visible terminal state.
