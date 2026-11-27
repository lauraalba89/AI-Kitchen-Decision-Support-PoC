
# AI Kitchen Decision Support – Proof of Concept

### Artificial Intelligence • Data Analytics • Demand Forecasting

## About the Project

This academic proof of concept explores how artificial intelligence and data integration can support decision-making in commercial kitchens.

The application combines historical pizza sales, recipe information, simulated inventory data, and demand forecasting to estimate preparation and purchasing requirements.

The project was developed as part of my Master of Information Technology studies at Whitecliffe, New Zealand.

## Project Objectives

- Explore AI applications in commercial kitchen operations.
- Integrate sales, recipes, and inventory information.
- Analyse historical sales patterns.
- Generate demand forecasts.
- Support preparation and purchasing decisions.

## Technologies Used

This project was developed through academic research, practical experimentation, and AI-assisted development.

- Python
- Streamlit
- Pandas and NumPy
- Google Gemini
- Amazon Chronos-2
- Excel datasets

## Project Structure

- `app.py` – Streamlit application interface.
- `backend.py` – Forecasting, ingredient calculations, and AI query processing.
- `config.py` – Dataset configuration.
- `DataSet/` – Historical sales and ingredient datasets.
- `Results/` – Saved forecasting results.
- `notebooks/` – Research experiments and analysis.
- `requirements.txt` – Python dependencies.

## Data Sources and Acknowledgements

Historical pizza sales and ingredient data were obtained from the following GitHub repository:

**Original repository:**  
https://github.com/pramodkondur/Dominoes-TimeseriesForecasting

Credit is given to the original repository and its contributor for making these resources available.

The datasets were cleaned and transformed for the purposes of this academic project.

Inventory information used in the proof of concept is simulated and should not be interpreted as actual business inventory records.

## How to Run the Application

1. Install Python.
2. Create and activate a virtual environment.
3. Install the required dependencies:

   pip install -r requirements.txt

4. Copy `.env.example` to `.env` and configure your own Gemini API key.
5. Run the application:

   streamlit run app.py

The forecasting model may require additional processing time and an internet connection for its initial download.

## Project Limitations

This application is an academic proof of concept rather than a production-ready commercial kitchen management system.

Forecasts are estimates and may differ from actual demand. Inventory data is simulated, and some purchasing calculations use simplified assumptions.

Further development, testing, and validation would be necessary before practical deployment.

## Future Development

- Improve data integration and automation.
- Expand forecasting capabilities.
- Develop more advanced inventory analysis.
- Improve the application interface.
- Test the system using additional datasets and operational scenarios.

## Author

**Laura Alba**

Master of Information Technology  
Whitecliffe, New Zealand

Auckland, New Zealand

**LinkedIn:**  
https://www.linkedin.com/in/laura-alba-it/
