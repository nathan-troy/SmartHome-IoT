# **Smart Home Utility & IoT Data Platform**

An end-to-end data platform built with **Python, Pandas, and DuckDB** that processes high-frequency IoT streaming telemetry logs alongside structured corporate property schemas. The architecture is modular and decoupled into distinct layers to mirror enterprise data engineering and data science lifecycles.

---

### **Architecture & Data Modelling**

The system processes data across three distinct isolation schemas within an embedded, high-performance DuckDB analytical database file (`smarthome_iot.db`).

#### **1. Ingestion Layer (`staging` schema)**
* **Extract & Load (E-L):** Raw dimension arrays (relational asset definitions) stored in CSV format and high-frequency operational streams (IoT telemetry payloads) stored in semi-structured JSON are ingested using independent Pandas frameworks.
* **Schema Isolation:** Data is initially loaded as loose, unmanipulated text strings into a staging area to allow for repeatable transformation pipelines without re-reading disk-bound files.

#### **2. Operational Database (`core` schema)**
* **Relational Integrity (3NF):** Staged strings are parsed, type-cast, and structured into a highly normalised **Third Normal Form (3NF)** relational database layout. 
* **Data Cleansing:** The transformation layer implements robust data quality rule sets, including vectorised text normalisation (standardising erratic string casings), explicit numerical type casting (`FLOAT`, `INTEGER`), and chronological UK Postcode string parsing to enforce spatial integrity. Mixed datetime formats (including UK format date structures) are handled using explicit parsing logic to capture accurate temporal intervals.

#### **3. Data Warehouse Layer (`analytics` schema)**
* **Dimensional Modelling (OLAP):** Normalised transaction tables are flattened into a highly performant **Star Schema Data Warehouse** designed for business intelligence queries.
* **Hourly Aggregations:** Minute-by-minute streaming telemetry is aggregated to an hourly grain. The processing layer uses SQL window functions and mathematical hashes (`MD5`) to generate immutable surrogate fact keys, mapping raw measurements into an analytical fact table (`fact_telemetry_hourly`) surrounded by wide dimension tables.

---

### **Technical Implementation Modules**

The pipeline codebase is split into decoupled, single-responsibility components:

* **`1_ingestion.py`:** Connects to the embedded analytical database engine and streams the raw unstructured files directly into isolated staging tables.
* **`2_transformation.py`:** Pulls from the staging tables, applies numerical type casting via NumPy/Pandas, standardises the spatial coordinates, and inserts the data into the production core database.
* **`3_view_metrics.py`:** Executes complex SQL joins and multi-level aggregations directly inside the terminal window to display immediate data profiling summaries.
* **`4_star_schema.py`:** Compiles the core relational tables into the analytical dimensional layout, aggregating metrics like average ambient temperatures and total power consumption.
* **`5_visualizations.py`:** Acts as the reporting presentation layer. It uses Matplotlib to handle time-series resampling, linear data interpolation to fill temporal gaps, and render dual-axis reporting visual charts tracking asset health profiles.

---
