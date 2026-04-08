# Heel Rise Data Analysis

## Overview

This repository provides a comprehensive suite of tools and Jupyter Notebooks designed for processing, analyzing, and extracting insights from heel rise exercise datasets. It offers an end-to-end workflow, streamlining the process from raw data ingestion to generating structured CSV outputs and visualizing the results.

## Project Structure

- **`data/`**: Contains the structured dataset directories organized by identifier.
- **`data_set_overview.ipynb`**: A Jupyter Notebook dedicated to exploratory data analysis, providing a high-level overview and visualization of the dataset.
- **`generate_csv.ipynb`**: A Jupyter Notebook focused on transforming, cleaning, and processing the raw data into a structured CSV format.
- **`helpers.py`**: A collection of utility functions and helper methods utilized across the notebooks and scripts to keep the code modular and clean.
- **`script.py`**: The core Python script for automated data processing tasks.
- **`results.csv`**: The aggregated output containing the final processed results.
- **`errors.csv`**: A log file tracking anomalies, missing data, or errors encountered during the data processing pipeline.

## Getting Started

### Prerequisites

Ensure you have Python installed on your system. The required Python packages and dependencies are listed in the `requirements.txt` file.

### Installation

1. Clone this repository to your local machine.
2. Install the necessary dependencies using `pip`:

```bash
pip install -r requirements.txt
```

### Usage

- Open and run the Jupyter Notebooks (`data_set_overview.ipynb` and `generate_csv.ipynb`) to interactively explore the data and generate outputs.
- Execute `script.py` for automated data processing and to reproduce the `results.csv` and `errors.csv` files.
