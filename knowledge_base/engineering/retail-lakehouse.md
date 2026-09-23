---
document_type: project
topic: retail-lakehouse
project: Retail Lakehouse Pipeline
author: Mohamed Taha Abo Heiba
portfolio_section: Projects
portfolio_url: https://my-portfolio.mohamed-aboheiba.workers.dev/#projects
source_url: https://github.com/MoTahaAboHeiba/retail-lakehouse-pipeline
status: complete
---

# Retail Lakehouse Pipeline — Mohamed Taha Abo Heiba

Mohamed Taha Abo Heiba built the Retail Lakehouse Pipeline as a data engineering project that loads retail source data into PostgreSQL, runs a Databricks ingestion job, transforms the data with dbt, and orchestrates the stages with Airflow. The local source checkout documents a sequential orchestration DAG and a dbt project with bronze source declarations, incremental silver models, ephemeral gold preparation models, snapshots, and a gold fact model.

GitHub: https://github.com/MoTahaAboHeiba/retail-lakehouse-pipeline
Source: https://motahaaboheiba.github.io/#projects

## Why This Project — Retail Lakehouse Pipeline

Mohamed Taha built this project to develop practical skill with dbt incremental models, snapshots, metadata-driven transformation, and Docker-based orchestration. The project is based on a retail data engineering tutorial structure, with engineering decisions and limitations documented on top of that structure.

## Source Systems — Retail Lakehouse Pipeline

The local source schema defines six PostgreSQL raw tables: `customers`, `stores`, `products`, `employees`, `orders`, and `order_items`. The loader maps six CSV files with those names to the corresponding `raw.*` tables and uses PostgreSQL `COPY` through `psycopg2`. The loader currently contains the placeholder connection string `your_connection_string_here`, so a real connection value is required before loading data.

### PostgreSQL Source — Retail Lakehouse Pipeline

The PostgreSQL source contains customer, store, product, employee, order, and order-item data. The source schema defines identifiers, descriptive attributes, timestamps, activity flags, and order or item measures such as `total_amount`, `quantity`, `unit_price`, and `line_amount`. The Airflow DAG does not load these CSV files directly. Its `ingest_cdc` task triggers an external Databricks job through the Databricks SDK and polls the job until it reaches a terminal state.

### Amazon S3 Source — Retail Lakehouse Pipeline

The local checkout does not contain the S3 ingestion implementation described by the portfolio documentation. No verified S3 source files, external-location configuration, or supplier-delivery model were found in the available source tree. This merged knowledge-base file therefore does not claim an S3 pipeline or supplier-delivery model as implemented local code.

## Medallion Architecture — Retail Lakehouse Pipeline

The dbt project declares the bronze source as catalog `walmart`, schema `bronze`, with six source tables: `orders`, `customers`, `products`, `order_items`, `stores`, and `employees`. The transformation layers below are the layers present in the local dbt project.

### Bronze Layer — Retail Lakehouse Pipeline

The bronze layer is represented by the dbt source declarations in `models/source/sources.yml`. The declarations provide named dbt sources for the six bronze tables instead of hardcoding catalog and schema references inside downstream models.

### Silver Technical Layer — Retail Lakehouse Pipeline

The local dbt project contains six silver technical models: `customers_t`, `employees_t`, `orders_t`, `order_items_t`, `products_t`, and `stores_t`. Each model is configured as an incremental model with a unique key and an updated-timestamp filter. The models provide the technical cleaned representation of the PostgreSQL source tables.

### Silver Business Layer — Retail Lakehouse Pipeline

The `obt_b` model builds a denormalized one-big-table representation by joining orders, customers, order items, products, employees, and stores. The project uses a structured configuration and Jinja generation for the business-layer selection and joins rather than repeating every join block manually.

### Gold Preparation Layer — Retail Lakehouse Pipeline

The gold directory contains ephemeral preparation models named `eph_customers`, `eph_employees`, `eph_orders`, `eph_products`, and `eph_stores`. These models prepare dimension inputs as inline dbt CTEs rather than persistent standalone warehouse tables.

### SCD Type 2 Snapshots — Retail Lakehouse Pipeline

The snapshots directory contains `dim_customers`, `dim_employees`, `dim_orders`, `dim_products`, and `dim_stores`. The snapshot configurations use timestamp-based SCD Type 2 tracking, business keys, and dbt-managed validity columns. The local snapshot configuration sets `dbt_valid_to_current` to `to_date('9999-12-31')`.

### Gold Layer — Retail Lakehouse Pipeline

The local source checkout contains one explicit gold fact model, `fact_orders`, under `models/gold/fact/`. It references the business-layer model and contains order-line measures and identifiers including `order_id`, `order_item_id`, `product_id`, `store_id`, `employee_id`, `customer_id`, `total_amount`, `quantity`, `unit_price`, and `line_amount`.

Based on the available local models, the verified schema description is a gold fact model fed by the business layer and supported by ephemeral dimension preparation and SCD Type 2 snapshots. A galaxy schema with two fact tables is described in portfolio and legacy KB content, but the second fact model was not present in this checkout and is not claimed here as verified source code.

## Orchestration — Retail Lakehouse Pipeline

The available Airflow DAG is `airflow_dbt_project/dags/orchestrate.py`. It defines the `orchestrate` DAG and creates these stages: `ingest_cdc`, `clean_target`, `source_freshness`, `silver_technical`, `silver_technical_tests`, `silver_business`, `silver_business_tests`, `gold_ephermeral`, `gold_dimensions`, and `gold_facts`.

### Airflow DAG Structure — Retail Lakehouse Pipeline

The dependency chain in the DAG is sequential: Databricks ingestion, target cleanup, source freshness, silver technical run, silver technical tests, silver business run, silver business tests, gold ephemeral run, snapshots, and gold fact run. The ingestion task creates a Databricks `WorkspaceClient`, triggers a configured job, polls its run state every five seconds, and raises an exception when the terminal result is not successful.

The DAG invokes dbt selectors named `silver_tech`, `silver_business`, and `gold/ephermeral`. The local directory names and the selector spelling should be checked before relying on the DAG in deployment. The available source does not contain a parallel DAG benchmark implementation.

### Parallel DAG Benchmark — Retail Lakehouse Pipeline

No benchmark calculation or parallel Airflow DAG was found in the available source checkout. The existing portfolio claim of a measured parallel speedup is therefore not used as a verified implementation fact in this document.

## Data Quality and Testing — Retail Lakehouse Pipeline

The local dbt test definitions contain five declared test definitions: four generic column assertions and one singular SQL test. The generic assertions cover `not_null` and `unique` checks on `products_t.product_id` and `orders_t.order_id`, with the product uniqueness assertion filtered to products where `price > 0`. The singular test checks joined key columns in the business-layer output and is configured with warning severity.

The verified count is **5 declared dbt test definitions**. The local source checkout does not verify a 123-test total.

## CI/CD — Retail Lakehouse Pipeline

No `.github/workflows/` directory or GitHub Actions workflow was found in the available retail source checkout. CI claims are therefore not included as verified implementation facts here.

## Engineering Decisions — Retail Lakehouse Pipeline

### Fan-Out and Grain Verification — Retail Lakehouse Pipeline

The existing project documentation describes an employee fan-out issue in which joining employees by `store_id` multiplied order-line rows because a store can have many employees and the source orders do not identify the employee who handled an order. The documented decision was to remove the unsupported employee-to-order join instead of fabricating a relationship. The standing practice is to compare row counts with the expected grain after a new or changed join.

The local DAG and dbt model files verify the current model names and transformations; the exact historical row counts described in legacy documentation are retained only as documented project context, not as a freshly measured result from this checkout.

### Latest-State Ingestion Limitation — Retail Lakehouse Pipeline

The Airflow task triggers an external Databricks ingestion job, but the available checkout does not include the Databricks job definition. The exact ingestion semantics and any CDC limitation cannot be verified from the local source files. This document does not claim true CDC or a specific production alternative without that missing configuration.

### Metadata-Driven Transformation — Retail Lakehouse Pipeline

The business-layer model uses structured configuration consumed by Jinja to generate its selected columns and joins. This keeps the repeated join structure in one generation path while retaining dbt `ref()` relationships for model lineage.

### Snapshot Strategy — Retail Lakehouse Pipeline

The local snapshot files use timestamp-based SCD Type 2 configuration for customers, employees, orders, products, and stores. The snapshot strategy preserves tracked versions through dbt validity columns. Any decision about supplier history is outside the verified model set because no supplier model was present in the local checkout.

## Tech Stack — Retail Lakehouse Pipeline

- PostgreSQL stores the six raw source tables defined by `walmart_schema.sql`.
- Python and `psycopg2` load the six CSV files through PostgreSQL `COPY`.
- Databricks SDK triggers and monitors the external ingestion job from Airflow.
- Apache Airflow defines and sequences the orchestration tasks.
- dbt models declare sources, build incremental silver models, generate the business model, prepare ephemeral gold inputs, run snapshots, and build the gold fact model.
- Docker files in the Airflow project support the orchestration environment.

## What I Would Build Next — Retail Lakehouse Pipeline

The next verified work items come from the implementation gaps visible in the checkout: provide real connection and Databricks configuration values, align DAG selectors with the actual dbt directory names, add the missing source freshness configuration or remove the freshness command, and add automated CI only after a workflow exists and its commands are verified.
