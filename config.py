
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "DataSet"

SALES_FILE = DATA_DIR / "3.Pizza_Sale_Cleaned.xlsx"
RECIPES_FILE = DATA_DIR / "4.Pizza_ingredients_cleaned.xlsx"
TIME_SERIES_FILE = DATA_DIR / "5.data_time_series.xlsx"
INVENTORY_FILE = BASE_DIR / "6.Simulated_Inventory.xlsx"
