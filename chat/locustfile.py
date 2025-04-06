from locust import HttpUser, TaskSet, task, between, events
import random
import time
import gevent


class ChatUser(HttpUser):
    wait_time = between(0.5, 1.5)

    def on_start(self):
        self.user_id = random.randint(4, 4)
        self.recipient_id = random.randint(5, 5)
        self.token_user = self.get_auth_token(id=self.user_id)
        self.message_sent = False
        self.start_time2 = 0

    def get_auth_token(self, id):
        auth_data = {
            "username": f"{id}",
            "password": "Qwerty4321"
        }
        response = self.client.post("/api_token_auth/", json=auth_data)
        if response.status_code != 200:
            raise Exception("Failed to authenticate")
        return response.json().get("token")

    @task
    def chat_task(self):
        # Запускаем GET запрос в отдельной зелёной нити
        greenlet_get = gevent.spawn(self.get_updates)

        # Выполняем POST запрос после некоторой задержки
        time.sleep(random.uniform(0.5, 1.5))  # Задержка перед отправкой сообщения
        self.send_message()

        # Ждем завершения GET запроса
        greenlet_get.join()

    def get_updates(self):
        start_time = time.time()
        while True:
            with self.client.get(f"/chat/messages/{self.recipient_id}", headers={"Authorization": f"Token {self.token_user}"}, catch_response=True) as response:
                if response.status_code == 200 and response.text != "":
                    response.success()
                    delivery_time = time.time() - self.start_time2
                    events.request.fire(
                        request_type="GET",
                        name="delivery_time",
                        response_time=delivery_time * 1000,  # в миллисекундах
                        response_length=len(response.content),
                    )
                    self.message_sent = False
                    break
                elif time.time() - start_time > 20:  # Если прошло более 20 секунд
                    response.failure("Timeout")
                    break
                time.sleep(1)  # Задержка перед повторной отправкой запроса

    def send_message(self):
        data = {
            "recipient_id": self.recipient_id,
            "text": "Hello, world!"
        }
        self.start_time2 = time.time()
        with self.client.post("/chat/messages/create/", json=data, headers={"Authorization": f"Token {self.token_user}"}, catch_response=True) as response:
            if response.status_code == 201:
                response.success()
                self.message_sent = True
            else:
                response.failure("Failed to send message")

# locust -f locustfile.py --host=http://localhost:8001
# uvicorn chat.asgi:application --host 127.0.0.1 --port 8001
# export DJANGO_SETTINGS_MODULE=chat.settings
