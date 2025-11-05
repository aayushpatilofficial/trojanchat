from flask import Flask, render_template, jsonify
from openai import OpenAI

app = Flask(__name__)

# Two AI clients (you’ll paste 2 API keys)
AI_A_CLIENT = OpenAI(api_key="YOUR_FIRST_OPENAI_KEY")
AI_B_CLIENT = OpenAI(api_key="YOUR_SECOND_OPENAI_KEY")

# Initial conversation
conversation = [
    {"role": "system", "content": "You are AI-A, curious and thoughtful."},
    {"role": "assistant", "content": "A: Hello, who are you?"}
]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat')
def chat():
    global conversation

    # AI-B replies
    b_response = AI_B_CLIENT.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation + [{"role": "user", "content": "Respond as AI-B in one line."}]
    )
    b_text = b_response.choices[0].message.content.strip()
    conversation.append({"role": "assistant", "content": f"B: {b_text}"})

    # AI-A replies
    a_response = AI_A_CLIENT.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation + [{"role": "user", "content": "Respond as AI-A in one line."}]
    )
    a_text = a_response.choices[0].message.content.strip()
    conversation.append({"role": "assistant", "content": f"A: {a_text}"})

    return jsonify(conversation[-6:])

if __name__ == '__main__':
    app.run(debug=True)
