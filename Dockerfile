FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    build-essential \
    postgresql-15 \
    postgresql-server-dev-15 \
  && rm -rf /var/lib/apt/lists/*

RUN git clone --branch v0.8.5 --depth 1 https://github.com/pgvector/pgvector.git /tmp/pgvector \
  && cd /tmp/pgvector \
  && make \
  && make install \
  && rm -rf /tmp/pgvector \
  && printf "listen_addresses = '*'\n" >> /etc/postgresql/15/main/postgresql.conf \
  && printf "host all all all trust\n" >> /etc/postgresql/15/main/pg_hba.conf

COPY docker/start-postgres.sh /usr/local/bin/start-postgres.sh

RUN chmod +x /usr/local/bin/start-postgres.sh

EXPOSE 5432

CMD ["/usr/local/bin/start-postgres.sh"]
