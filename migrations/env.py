import os
import sys
from logging.config import fileConfig
from dotenv import load_dotenv

from alembic import context
from sqlalchemy import engine_from_config, pool

# 1) Importa o seu Base e models, para o Alembic saber quais tabelas existem
from database import Base
from app.adapters.driven import models

# 3) Obtemos a configuração do Alembic
config = context.config
load_dotenv()

# 4) Lê as variáveis do ambiente (que podem vir do .env)
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# 5) Monta a URL do banco dinamicamente
database_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 6) Sobrescreve a sqlalchemy.url que está no alembic.ini
config.set_main_option("sqlalchemy.url", database_url)

# 7) Se tivermos config para logs, carrega config de logging do arquivo ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 8) Aponta o Alembic para o metadata do seu projeto (para autogenerate)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Rodar migrações em modo 'offline':
    Apenas gera/roda o SQL sem precisar de conexão real com o BD.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Rodar migrações em modo 'online':
    Cria Engine e conecta de verdade no BD.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


# Alembic decide, em tempo de execução, se é offline ou online
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
