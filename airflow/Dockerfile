ARG AIRFLOW_VERSION=3.1.6

FROM apache/airflow:${AIRFLOW_VERSION}

USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         openjdk-17-jre-headless \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=my_conn_string

# Create directories for DAGS 
RUN mkdir -p /opt/airflow/dags /opt/airflow/plugins /opt/airflow/config  /opt/airflow/logs \
    && chown -R airflow: /opt/airflow/dags /opt/airflow/plugins /opt/airflow/config /opt/airflow/logs


# Copiar DAGs e plugins
COPY dags /opt/airflow/dags
COPY plugins /opt/airflow/plugins

USER airflow

# Instalar dependências Python adicionais
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt


