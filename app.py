from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
import os
import stripe

app = Flask(__name__, template_folder='templates')
app.secret_key = 'Hack'  

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

stripe.api_key = '@task'
STRIPE_PUBLIC_KEY = '@open'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        users = {
            'hell': {'password': 'wor', 'pro_license': False, 'todos': []},
            'john': {'password': 'doe', 'pro_license': True, 'todos': []}
        }
        if 'username' not in session:
            print("User not in session, redirecting to login")
            return redirect(url_for('login'))
        if not users.get(session['username'], {}).get('pro_license', False):
            print("User does not have pro_license, redirecting to index")
            return f(*args, **kwargs)
        return f(*args, **kwargs)
    return decorated_function

users = {
    'hell': {'password': 'wor', 'pro_license': False, 'todos': []},
    'john': {'password': 'doe', 'pro_license': True, 'todos': []}
}
uploaded_files = ['']
stripe_product_id = '24'
stripe_price_id = '#100'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Debugging print statements
        print(f"Entered username: {username}, Entered password: {password}")

        # Check if the username exists
        if username in users:
            # Check if the entered password matches the stored password
            if users[username]['password'] == password:
                session['username'] = username
                print("Login successful")
                return redirect(url_for('index'))
            else:
                print("Incorrect password")
        else:
            print("Username not found")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/')
@login_required
def index():
    user = users[session['username']]
    return render_template('index.html', todos=user['todos'], users=users, uploaded_success=session.pop('uploaded_success', False), uploaded_files=uploaded_files)

@app.route('/add', methods=['POST'])
@login_required
def add():
    user = users[session['username']]
    title = request.form['title']
    description = request.form['description']
    time = request.form['time']
    new_todo = {'id': len(user['todos']), 'title': title, 'description': description, 'time': time, 'done': False}
    user['todos'].append(new_todo)
    return redirect(url_for('index'))

@app.route('/edit/<int:index>', methods=['GET', 'POST'])
@login_required
def edit(index):
    user = users[session['username']]
    todo = user['todos'][index]
    if request.method == 'POST':
        todo['title'] = request.form['title']
        todo['description'] = request.form['description']
        todo['time'] = request.form['time']
        return redirect(url_for('index'))
    else:
        return render_template('edit.html', todo=todo, index=index)

@app.route('/check/<int:index>')
@login_required
def check(index):
    user = users[session['username']]
    user['todos'][index]['done'] = not user['todos'][index]['done']
    return redirect(url_for('index'))

@app.route('/delete/<int:index>')
@login_required
def delete(index):
    user = users[session['username']]
    del user['todos'][index]
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']

    if file.filename == '':
        return redirect(url_for('index'))

    if file:
        # Create the 'uploads' directory if it doesn't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)

        # You can add the uploaded filename to the list of uploaded_files
        uploaded_files.append(file.filename)

        # Set a session variable to indicate successful upload
        session['uploaded_success'] = True

        return redirect(url_for('index'))

@app.route('/pro_license_purchase', methods=['GET', 'POST'])
@login_required
def pro_license_purchase():
    if request.method == 'POST':
        # Create a checkout session with Stripe
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': stripe_price_id,
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('index', _external=True) + '?pro_license=success',
            cancel_url=url_for('index', _external=True) + '?pro_license=cancel',
        )
        return redirect(session.url, code=303)
    else:
        return render_template('pro_license_purchase.html')  
if __name__ == '__main__':
    app.run(debug=True)
