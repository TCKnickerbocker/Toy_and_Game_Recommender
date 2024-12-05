### TODO: make operational
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

with DAG(
    dag_id='amazon_etl_pipeline',
    default_args=default_args,
    description='ETL pipeline for Kids Toys Reviews',
    schedule_interval='@daily',
    start_date=days_ago(1),
    catchup=False,
) as dag:
    
    etl_task = BashOperator(
        task_id='run_etl_pipeline',
        bash_command='python /app/src/etl/etl_pipeline.py'
    )

etl_task
