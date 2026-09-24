# Rollback Contract

Stop new imports and ERP deliveries, retain the outbox, and revert only the application deployment. Database migrations require an explicit tested downgrade or a forward repair; never restore a production database from an unverified snapshot.
