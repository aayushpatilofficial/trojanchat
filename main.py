from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

@app.route('/')
def index():
    return render_template('index.html')

# receive command from any client and broadcast to all
@socketio.on('send_command')
def handle_command(data):
    command = data.get('command')
    emit('receive_command', {'command': command}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
