from alembic import context
from database import engine
from models import Base

target_metadata = Base.metadata

if context.is_offline_mode():
    context.configure(url=engine.url, target_metadata=target_metadata,
                      literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()
else:
    def run_migrations(connection):
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

    # Tests can supply a connection inside an isolated PostgreSQL schema.
    connection = context.config.attributes.get("connection")
    if connection is not None:
        run_migrations(connection)
    else:
        with engine.connect() as connection:
            run_migrations(connection)
