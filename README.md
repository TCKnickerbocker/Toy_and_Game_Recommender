# Amazon Toy and Games Recommender
## Thomas Knickerbocker, Owen Ratgen, Yashas Acharya
<br>

### How to Run the Project
1. Open a terminal
2. Go to the src/frontend folder
3. Run command ```npm run start```
4. Open another terminal
5. Go to the src/api folder
6. Run command ```python3 index.py```

### [Project Plan] (https://docs.google.com/document/d/1dajEkWcu0pIWDITtmJ7vQ9KNjShbRnZYYVwgbx_ofoY/edit?tab=t.gzr8m69bdr1d)
### [Raw Data Structure] (https://docs.google.com/spreadsheets/d/1eK1lWKYCCQQE_UpZJ0EMTd06sOM6jStpfcECJd98mFQ/edit?gid=609464681#gid=609464681)

^ Feel free to add/edit these, as well as all files in this repo. Let's get it boys.

Current File Tree:

.
├── README.md  
├── configs  
│   └── raw_reviews_config.json  
├── data  
│   ├── logs  
│   ├── preprocessed  
│   └── raw  
│       ├── Toys_and_Games.jsonl  
│       └── meta_Toys_and_Games.jsonl  
├── docker-compose.yaml  
├── requirements.txt  
├── src  
│   ├── api  
│   │   └── inference_api.py  
│   ├── deployment  
│   │   ├── airflow_dag.py  
│   │   ├── docker  
│   │   │   ├── Dockerfile  
│   │   │   └── Dockerfile.api  
│   │   ├── grafana-deployment.yaml  
│   │   ├── kubernetes  
│   │   │   └── flask-api-deployment.yaml  
│   │   └── spark-cluster-deployment.yaml  
│   ├── etl  
│   │   ├── etl_pipeline.py  
│   │   ├── etl_pipeline_v2.py  
│   │   ├── sentiment_analysis.py  
│   │   ├── snowflake_connector.py  
│   │   ├── some_nlp_file.py  
│   │   └── spark_config.py  
│   ├── examples  
│   │   └── example_read_from_azure.py  
│   ├── models  
│   │   └── train_model.py  
│   └── monitoring  
│       └── prometheus-config.yaml  
└── tests  

16 directories, 22 files

### Put ALL Login info in .env, ensure is in gitignore


