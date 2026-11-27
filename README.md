# AI Kitchen Decision Support – Proof of Concept

### Artificial Intelligence | Data Analytics | Demand Forecasting | Commercial Kitchen Operations

## About the Project

AI Kitchen Decision Support is an academic proof of concept (PoC) exploring how artificial intelligence, data analytics, and integrated information systems can support operational decision-making in commercial kitchens.

The application integrates historical pizza sales, recipe information, simulated inventory records, and AI-based demand forecasting to help estimate food preparation quantities, ingredient requirements, and purchasing needs.

The project was developed as part of my **Master of Information Technology at Whitecliffe, New Zealand**, combining my professional experience in commercial kitchen operations with my studies in information technology.

The objective is to explore how fragmented operational data can be transformed into useful information to support kitchen planning and decision-making.

## Project Objectives

- Explore practical applications of artificial intelligence in commercial kitchens.
- Integrate sales, recipes, and inventory information.
- Analyse historical sales patterns and product demand.
- Compare forecasting approaches using experimental analysis.
- Generate AI-based demand forecasts.
- Translate predicted demand into ingredient and preparation requirements.
- Explore how natural-language queries can support access to operational information.
- Demonstrate the potential of AI-assisted decision support in food-service environments.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Application development, data processing, and business logic |
| Streamlit | Interactive application interface |
| Pandas and NumPy | Data cleaning, transformation, and calculations |
| Google Gemini | Natural-language query interpretation |
| Amazon Chronos-2 | Time-series demand forecasting |
| Jupyter Notebook | Data exploration, preprocessing, and model experimentation |
| Excel | Historical datasets, recipe information, and simulated inventory |
| Random Forest | Experimental forecasting comparison |
| TimeGPT | Experimental forecasting comparison |

The project was developed through academic research, practical experimentation, and AI-assisted development.

## Development Methodology

The proof of concept was developed through several stages.

### 1. Data Exploration and Preparation

Historical pizza sales and ingredient datasets were examined and prepared for analysis.

The Jupyter Notebooks document activities including:

- Data exploration and quality assessment.
- Identification and treatment of missing values and inconsistencies.
- Data cleaning and transformation.
- Preparation of time-series data.
- Examination of historical demand patterns.
- Preparation of information for forecasting and operational calculations.

These activities established the data foundation for the proof of concept.

### 2. Forecasting Model Comparison

Experimental forecasting analysis was conducted to explore different approaches to predicting product demand.

The comparison included:

- Random Forest
- Amazon Chronos-2
- TimeGPT

The experiments included expanding-window validation and examination of forecasting results.

The purpose was to investigate the suitability of different forecasting approaches for historical sales data and support the technical development of the application.

The experimental work is documented in the `notebooks/` directory, with saved forecasting outputs available in `Results/`.

### 3. Data Integration

The application combines information from multiple operational datasets:

- Historical pizza sales.
- Pizza recipes and ingredient quantities.
- Time-series sales information.
- Simulated inventory records.

Python-based processing connects these sources to support demand forecasting and ingredient calculations.

### 4. AI Integration

Two AI technologies support different functions within the proof of concept.

**Amazon Chronos-2 – Demand Forecasting**

Chronos-2 is used to generate forecasts from historical time-series data.

The application uses predicted demand to support estimates of pizza preparation quantities and associated ingredient requirements.

**Google Gemini – Natural-Language Interpretation**

Gemini is used to interpret natural-language queries submitted through the application.

This allows the prototype to explore a more accessible way of interacting with operational information, rather than relying exclusively on manual data analysis.

### 5. Preparation and Inventory Calculations

The application connects forecasted pizza demand with recipe information to estimate ingredient requirements.

Simulated inventory records are used to explore how available stock may affect preparation and purchasing calculations.

These calculations depend on the available data and simplified assumptions implemented in the proof of concept.

## Application Workflow

The following sequence summarises the main components of the system:

1. **Data Input:** Historical sales, recipes, and simulated inventory datasets are loaded.
2. **Data Processing:** Python prepares and connects the information.
3. **Demand Forecasting:** Chronos-2 generates predictions using historical sales data.
4. **Ingredient Calculations:** Predicted demand is connected to recipe quantities.
5. **Inventory Analysis:** Simulated stock information is used to support preparation and purchasing estimates.
6. **User Interaction:** Streamlit provides the application interface, while Gemini supports natural-language query interpretation.
7. **Decision Support:** The application presents operational information intended to assist kitchen planning.

## Project Structure

```text
AI-Kitchen-Decision-Support-PoC/
│
├── DataSet/
│   └── Historical sales, recipe and time-series datasets
│
├── Results/
│   └── Saved forecasting results
│
├── notebooks/
│   └── Data analysis, preprocessing and model comparisons
│
├── app.py
├── backend.py
├── config.py
│
├── 6.Simulated_Inventory.xlsx
├── 7.Simulated_Inventory_2016.xlsx
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### Main Files

- `app.py` – Streamlit user interface and interaction components.
- `backend.py` – Forecasting, ingredient calculations, inventory processing, and AI query handling.
- `config.py` – Dataset locations and configuration.
- `DataSet/` – Historical sales, recipe, and processed datasets.
- `Results/` – Forecasting outputs generated during experimentation.
- `notebooks/` – Jupyter Notebooks documenting data preparation, exploratory analysis, and forecasting experiments.
- `6.Simulated_Inventory.xlsx` – Simulated inventory dataset.
- `7.Simulated_Inventory_2016.xlsx` – Simulated inventory dataset for 2016.
- `requirements.txt` – Python package dependencies.
- `.env.example` – Template for configuring the required API credentials.
- `.gitignore` – Rules for excluding sensitive configuration and temporary files from version control.

## Data Sources and Acknowledgements

Historical pizza sales and ingredient information were obtained from the following publicly available GitHub repository:

**Original dataset repository:**

https://github.com/pramodkondur/Dominoes-TimeseriesForecasting

Credit is given to the original repository and its contributor for making these resources available.

The datasets were cleaned, transformed, and prepared for the purposes of this academic project.

Inventory datasets used in the proof of concept are simulated and should not be interpreted as actual business inventory records.

The project does not represent a production deployment or an operational system used by a commercial kitchen.

## How to Run the Application

### 1. Requirements

- Python installed on your computer.
- An internet connection for downloading the forecasting model when required.
- A Google Gemini API key.
- The project files and datasets.

### 2. Clone the Repository

```bash
git clone https://github.com/lauraalba89/AI-Kitchen-Decision-Support-PoC.git
cd AI-Kitchen-Decision-Support-PoC
```

Alternatively, download the repository as a ZIP file and extract it.

### 3. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate the environment.

**Windows:**

```powershell
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

The forecasting model may require additional processing time and computational resources, particularly during its initial download and loading.

### 5. Configure Environment Variables

Copy `.env.example` to a new file named `.env`.

Add your own Gemini API key:

```dotenv
GEMINI_API_KEY=your_own_gemini_api_key
```

The `.env` file contains private configuration information and must not be uploaded to a public repository.

A Nixtla API key may be required for optional TimeGPT experiments documented in the forecasting comparison notebook. It is not part of the standard application setup.

### 6. Run the Application

From the project's main directory, execute:

```bash
streamlit run app.py
```

Streamlit will provide a local address for accessing the application through a web browser.

**Note:** These instructions describe the intended local setup. Successful execution depends on the installed environment, available resources, API access, and compatible package versions.

## Project Limitations

This application is an academic proof of concept rather than a production-ready commercial kitchen management system.

The following limitations apply:

- Forecasts are estimates and may differ from actual demand.
- Inventory information is simulated rather than collected from a live commercial kitchen.
- Some ingredient and purchasing calculations rely on simplified assumptions.
- Forecasting performance may vary across datasets and operating conditions.
- AI-generated interpretations require appropriate validation.
- The application has not been established as a fully tested production system.
- Additional integration, security assessment, testing, and validation would be necessary before commercial deployment.

The project demonstrates technical feasibility and explores opportunities for AI-supported operational decision-making.

## Future Development

Potential areas for further development include:

- Integration with real point-of-sale and inventory management systems.
- Automated data collection and updating.
- Improved forecasting evaluation across additional datasets.
- More advanced inventory and purchasing analysis.
- Improved handling of real-time operational information.
- Enhanced user interface and reporting capabilities.
- Additional testing with real commercial kitchen scenarios.
- Evaluation of usability, reliability, and practical business value.

## Academic and Professional Context

This project reflects the intersection of commercial kitchen operations, information technology, and applied artificial intelligence.

My professional experience in the food-service industry provided practical context for identifying operational challenges involving fragmented information, manual processes, and preparation planning.

Through my Master of Information Technology studies, I explored how data integration, forecasting models, and AI-supported interfaces could contribute to addressing these challenges.

The proof of concept represents an application of academic learning to a practical industry problem.

## Author

**Laura Alba**

Master of Information Technology  
Whitecliffe, New Zealand

**LinkedIn:** https://www.linkedin.com/in/laura-alba-it/

**GitHub:** https://github.com/lauraalba89

---

*Academic Proof of Concept | Artificial Intelligence | Data Analytics | Commercial Kitchen Decision Support*
Auckland, New Zealand

**LinkedIn:**  
https://www.linkedin.com/in/laura-alba-it/
