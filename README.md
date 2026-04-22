# ProGPT - Free ChatGPT API

![ChatGPT](https://img.shields.io/badge/chatGPT-74aa9c?style=for-the-badge&logo=openai&logoColor=white)

I reverse engineered **ChatGPT's Free Web API** and made this simple python package.

Both **Generative** & **Conversation** modes are supported.

## 📦 Installation
```python
$ pip install progpt
```

### 🔑 How to get *access_token*?
In your browser:
1. Login to [**chat.openai.com**](https://chat.openai.com)
2. Open [**this page**](https://chat.openai.com/api/auth/session), and you'll see **JSON** data
3. Copy value of **accessToken**


### 🚀 Generative Mode
Answers individual prompts, doesn't remember past messages.

```python
from ProGPT import Generative

bot = Generative(access_token)

print(bot.prompt("who invented electricity?"))
```

### 🍿 Conversation Mode
Creates a conversation thread and remembers your chat history.

```python
from ProGPT import Conversation

bot = Conversation(access_token)

print(bot.prompt("hello"))
print(bot.prompt("how are you?"))
```

## ⚡ Rate Limits
To overcome the free tier's rate limits:
- Add time gap between prompts
- Use multiple accounts

## 👮 Legal
This is a third party library and not associated with OpenAI or ChatGPT. It's strictly for educational purposes. You are liable for all the actions you take.
