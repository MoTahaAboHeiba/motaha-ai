# Data Warehouse

Mohamed Taha built this SQL Data Warehouse project to apply data-warehousing
concepts from raw source data through transformation and analytical modeling.

**Mohamed Taha Abo Heiba** — Data Engineer.

I built this project to apply what I've learned in data warehousing —
from working with raw data to producing business-ready insights.
It demonstrates an end-to-end data pipeline including data ingestion,
transformation, and modeling, following industry best practices.

- ETL processes
- Data modeling

---

## Data Architecture

The data architecture follows **Medallion Architecture** with Bronze,
Silver, and Gold layers:

1. **Bronze Layer**: Stores raw data as-is from the source systems.
   Data is ingested from CSV files into a SQL Server database.
2. **Silver Layer**: Data cleansing, standardization, and normalization
   to prepare data for analysis.
3. **Gold Layer**: Business-ready data modeled into a star schema
   for reporting and analytics.

---

## Project Overview

1. **Data Architecture**: Designing a Modern Data Warehouse using
   Medallion Architecture Bronze, Silver, and Gold layers.
2. **ETL Pipelines**: Extracting, transforming, and loading data
   from source systems into the warehouse.
3. **Data Modeling**: Developing fact and dimension tables optimized
   for analytical queries.

---

## Technologies Used

1. **SQL Server** — Data storage, transformation, and processing
2. **SQL** — ETL pipelines and data modeling logic
3. **Draw.io** — Architecture and data model documentation

---

## Project Requirements

### Building the Data Warehouse (Data Engineering)

#### Objective

Develop a modern data warehouse using SQL Server to consolidate sales
data, enabling analytical reporting and informed decision-making.

#### Specifications

- **Data Sources**: Import data from two source systems (ERP and CRM)
  provided as CSV files.
- **Data Quality**: Cleanse and resolve data quality issues before
  analysis.
- **Integration**: Combine both sources into a single, user-friendly
  data model designed for analytical queries.
- **Scope**: Focus on the latest dataset only; historization of data
  is not required.
- **Documentation**: Provide clear documentation of the data model
  to support both business stakeholders and analytics teams.

---

## Author

**Mohamed Taha Abo Heiba**

[Portfolio](https://motahaaboheiba.github.io) |
[LinkedIn](https://linkedin.com/in/mohamed-taha-abo-heiba) |
[GitHub](https://github.com/MoTahaAboHeiba)