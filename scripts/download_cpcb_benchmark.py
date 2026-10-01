"""Download the public CPCB-derived benchmark used for optional model training.
Run explicitly; the repository does not vendor third-party dataset bytes.
"""
from pathlib import Path
from urllib.request import urlretrieve
URL='https://raw.githubusercontent.com/KunalLatkar/RiverWaterQualityDataset/main/RiverWaterQualityOverYears_PreprocessedData.csv'
OUT=Path(__file__).resolve().parents[1]/'data/external/cpcb_india_2012_2023.csv'
OUT.parent.mkdir(parents=True,exist_ok=True)
urlretrieve(URL,OUT)
print(f'Downloaded {OUT}')
