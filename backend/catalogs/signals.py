def seed_catalogs_after_migrate(sender, **kwargs):
    from catalogs.seeds import seed_system_catalogs

    seed_system_catalogs()
