from locust import HttpUser, TaskSet, task
import requests


class UserBehavior(TaskSet):

# def get_auth0_token(self):
#     # Request a token from Auth0
#     url = f"https://{domain}/oauth/token"
#     payload = {
#         "client_id": client_id,
#         "client_secret": client_secret,
#         "audience": audience,
#         "username": 
#         "grant_type": "client_credentials"
#     }
#     response = requests.post(url, json=payload)
#     print(client_id)
#     print(client_secret)
#     print(audience)

#     if response.status_code == 200:
#         token = response.json()["access_token"]
#     else:
#         raise Exception(f"Failed to get Auth0 token: {response.text}")

# def on_start(self):
#     if not token:
#         self.get_auth0_token()

#     headers = {
#         "Authorization": f"Bearer {self.token}"
#     }
#     response = self.client.get("/recommend", headers=headers)

#     if response.status_code == 200:
#         print("Successfully authenticated and accessed the endpoint!")
#     else:
#         print(f"Failed to access endpoint: {response.status_code}, {response.text}")

    # @task(1)
    # def initial_products(self):
    #     self.client.get("/api/initial_products")

    # @task(2)
    # def submit_form(self):
    #     self.client.post("/api/user_ratings", json={"user_id": "1", "product_id": "2", "rating": "3.5", "favorite": "0"})

    @task(1)
    def model_1(self):
        self.client.get("/api/most_similar_products") 

    @task(2)
    def model_2(self):
        self.client.get("/api/recommend_products_sentiment_model") 

    @task(3)
    def model_3(self):
        self.client.get("/api/recommend_products_llm_model") 

    @task(4)
    def model_4(self):
        self.client.get("/api/recommend_products_similarity_oyt_llm_combined_model") 


class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    min_wait = 100  # ms
    max_wait = 5000  # ms



# TO RUN: $)locust
