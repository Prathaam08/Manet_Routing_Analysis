# MANET Routing Performance Analysis

This project aims to analyze the performance of Mobile Ad-hoc Networks (MANETs) based on various network parameters and routing protocols. It uses a simulated dataset (assumed to be similar to the Kaggle "MANET Routing Dataset") to build a machine learning model that can predict network performance.

## Project Structure

The project follows a standard data science project structure:

- `data/`: Stores raw and processed datasets.
- `notebooks/`: Contains Jupyter notebooks for exploratory data analysis and experimentation.
- `src/`: Houses all Python source code, organized into modules for data handling, feature engineering, model training, prediction, visualization, and utilities.
- `models/`: Stores trained machine learning models.
- `reports/`: Contains generated figures and final reports.
- `config/`: Configuration files for project parameters.
- `tests/`: Unit tests for code modules.
- `requirements.txt`: Lists all Python dependencies.
- `main.py`: The main entry point to run the entire pipeline.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your_username/manet_routing_analysis.git](https://github.com/your_username/manet_routing_analysis.git)
    cd manet_routing_analysis
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Place your raw data:**
    Ensure your `manet_routing_data.csv` file is placed in the `data/raw/` directory. If your dataset has a different name, update `config/config.yaml` accordingly.

2.  **Run the full pipeline:**
    ```bash
    python main.py
    ```
    This script will:
    - Load and preprocess the data.
    - Train a machine learning model.
    - Evaluate the model.
    - Save the trained model and evaluation results.

3.  **Explore data and results:**
    - Open `notebooks/exploratory_data_analysis.ipynb` to understand the dataset.
    - Check `reports/figures/` for generated visualizations.
    - Review `reports/final_report.md` for a summary of findings.

## Dataset Assumption

Due to the inaccessibility of the specified Kaggle dataset, this project assumes the `manet_routing_data.csv` file has the following structure (or similar), where `Network_Performance_Class` is the target variable for classification:

| num_nodes | mobility_model | node_speed_mps | pause_time_s | simulation_area_m2 | routing_protocol | traffic_type | packet_size_bytes | transmission_range_m | packet_delivery_ratio | throughput_kbps | end_to_end_delay_ms | packet_loss_rate | routing_overhead | Network_Performance_Class |
| :-------- | :------------- | :------------- | :----------- | :----------------- | :--------------- | :----------- | :---------------- | :------------------- | :-------------------- | :-------------- | :------------------ | :--------------- | :--------------- | :------------------------ |
| 50        | Random Waypoint| 10             | 0            | 1000x1000          | AODV             | CBR          | 512               | 250                  | 0.95                  | 800             | 50                  | 0.05             | 1200             | High                      |
| 30        | Random Direction| 5             | 10           | 500x500            | DSDV             | FTP          | 1024              | 200                  | 0.70                  | 300             | 150                 | 0.30             | 800              | Low                       |
| ...       | ...            | ...          | ...          | ...                | ...              | ...          | ...               | ...                  | ...                   | ...             | ...                 | ...              | ...              | ...                       |

## Contributing

Feel free to open issues or submit pull requests.



import new dataset
delete all the file in models
delete the reports folder in notebooks
delete the pictures in reports/figures 
clear the data in final_report.md
correct the path for eda in confi.yaml
