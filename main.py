import queue
import threading
import time
from ollama import Client
import json

class Message:
    def __init__(self, name, content):
        self.said_by = name
        self.content = content

    def user_msg(self):
        return {
            "role": "user",
            "content": self.content
        }

    def assistant_msg(self):
        return {
            "role": "assistant",
            "content": self.content
        }

class Philosopher:
    def __init__(self, path=""):
        phil = json.load(open(path, "r"))
        self.name = phil["name"]
        self.description = phil["description"]
        self.messages = [
            {
                "role": "system",
                "content": self.description
            }
        ]
        self.client = Client(host='http://localhost:11434')

    def listen(self, msg):
        if msg.said_by == self.name:
            # NOTE: Ignore your own messages
            return None

        self.messages.append(msg.user_msg())
        response = self.client.chat(
            model='llama3.2:latest',
            messages=self.messages,
            options={'num_predict': 30}
        )

        response_msg = Message(self.name, response['message']['content'])
        self.messages.append(response_msg.assistant_msg())

        return response_msg

    def __str__(self):
        return f'<{self.name}>'

class Dialogue:
    def __init__(self):
        self.queue = queue.Queue()
        self.interlocutors = []

    def add_interlocutor(self, interlocutor):
        print(f'Adding {interlocutor}')
        self.interlocutors.append(interlocutor)

    def listen(self):
        while True:
            try:
                msg = self.queue.get(timeout=2)
                print(f'{msg.said_by}: {msg.content}')
            except queue.Empty:
                print("queue empty")
                break

            for interlocutor in self.interlocutors:
                new_msg = interlocutor.listen(msg)
                if new_msg:
                    self.queue.put(new_msg)

            self.queue.task_done()

    def send_message(self, msg):
        self.queue.put(msg)


def start_dialogue(topic, dialogue_time=100):
    aristotle = Philosopher("./philosophers/aristotle.json")
    plato = Philosopher("./philosophers/plato.json")
    socrates = Philosopher("./philosophers/socrates.json")

    dialogue = Dialogue()
    dialogue.add_interlocutor(aristotle)
    dialogue.add_interlocutor(plato)
    dialogue.add_interlocutor(socrates)

    dialogue_thread = threading.Thread(target=dialogue.listen, daemon=True)
    dialogue_thread.start()

    start_message = Message("user", f"Let's discuss: {topic}")

    dialogue.send_message(start_message)

    time.sleep(dialogue_time)

if __name__ == '__main__':
    topic = "The problem of evil"
    start_dialogue(topic, 30)