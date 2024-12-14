from locust import HttpUser, TaskSet, task

class UserBehavior(TaskSet):
    @task(1)
    def view_home(self):
        self.client.get("/")

    @task(2)
    def submit_form(self):
        self.client.post("/submit", json={"key": "value"})

class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    min_wait = 1000  # ms
    max_wait = 5000  # ms

# locust -f test_script_1.py --host=http://localhost:4000
