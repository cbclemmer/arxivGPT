import openai
import tiktoken

import os
import json
import time
import datetime
from typing import List

from util import open_file, save_file
from objects import Message, Conversation

class GptChat:
    messages: List[Message]
    conversations: List[Conversation]

    def __init__(self, system_prompt_file: str) -> None:
        self.system_prompt = open_file('prompts/' + system_prompt_file + '.prompt')
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        self.system_prompt_tokens = len(self.encoding.encode(self.system_prompt))
        self.messages = []
        self.conversations = []
        self.reset_chat()
        self.total_tokens = 0

    def save_completions(self, file_name):
        if len(self.conversations) == 0:
            return
        text = ''
        for completion in self.conversations:
            text += json.dumps(completion.to_object()) + '\n'
        today = datetime.date.today().strftime("%Y-%m-%d")

        if not os.path.exists('completions'):
            os.mkdir('completions')
        save_file(f'completions/{file_name}_{today}.json', text)

    def add_message(self, message: str, role: str):
        self.messages.append(Message(role, message))

    def reset_chat(self):
        if len(self.messages) > 1:
            self.conversations.append(Conversation(self.messages))
        self.messages = [ ]
        self.add_message(self.system_prompt, "system")

    def get_message_tokens(self) -> int:
        message_tokens = 0
        for m in self.messages:
            message_tokens += len(self.encoding.encode(m.content))
        return message_tokens

    def send(self, message: str, max_tokens=100) -> str:
        message_tokens = self.get_message_tokens()
        message_tokens += len(self.encoding.encode(message))
        print(f"Sending chat with {message_tokens} tokens")
        
        if message_tokens >= 4096 - 200:
            raise "Chat Error too many tokens"
        
        self.add_message(message, "user")
        
        defaultConfig = {
            "model": 'gpt-3.5-turbo',
            "max_tokens": max_tokens,
            "messages": Conversation(self.messages).to_object(),
            "temperature": 0.5
        }

        try:
            res = openai.ChatCompletion.create(**defaultConfig)
        except:
            print('Error when sending chat, retrying in one minute')
            time.sleep(60)
            self.messages = self.messages[:-1]
            self.send(message, max_tokens)
        msg = res.choices[0].message.content.strip()
        print(f"GPT API responded with {res.usage.completion_tokens} tokens")
        self.add_message(msg, "assistant")
        self.total_tokens += res.usage.total_tokens
        return msg