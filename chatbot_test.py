import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

from server import DisasterChatbot

bot = DisasterChatbot()

questions = [
    'What does this project do?',
    'How are flood risks predicted?',
    'What safety steps should I take during an earthquake?',
    'What is the SafeSphere dashboard?',
]

print('=== PROJECT ASSISTANT CHATBOT TEST ===\n')
for q in questions:
    answer = bot.get_contextual_response(q, {})
    print(f'Q: {q}')
    print(f'A: {answer[:200]}')
    print()

print('=== CHATBOT TEST COMPLETE ===')
