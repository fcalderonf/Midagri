├── SISUE_UPDATE_PARCELA.py
├── config/
│   └── settings.json
├── logs/
│   └── sisue_update_parcela.log
├── data/
│   └── input/            # Datos de entrada
│   └── output/           # Resultados generados
└── README.md


Versión recomendada: Python 3.9 o superior

Verifique su versión:python --version

Librerías Necesarias
pip install arcpy
pip install pandas
pip install requests
pip install python-dotenv

config/settings.json
{
  "gdb_path": "C:/GIS/Geodatabase/amb_corporativa.sde",
  "feature_class": "PARCELAS",
  "log_level": "INFO",
  "overwrite": true,
  "input_folder": "./data/input",
  "output_folder": "./data/output"
}

Ejecución directa: python SISUE_UPDATE_PARCELA.py

Archivo de log: /logs/sisue_update_parcela.log