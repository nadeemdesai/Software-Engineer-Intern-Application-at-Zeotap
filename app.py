import sqlite3
import json
import ast
from flask import Flask, request, render_template, jsonify

# Define the Node class
class Node:
    def __init__(self, type, left=None, right=None, value=None, func_name=None, args=None):
        self.type = type
        self.left = left
        self.right = right
        self.value = value
        self.func_name = func_name  # Name of the function
        self.args = args or []  # List of arguments for the function

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('rule_engine.db', check_same_thread=False)
cursor = conn.cursor()

# Create the rules table
cursor.execute('''
CREATE TABLE IF NOT EXISTS rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_string TEXT NOT NULL,
    rule_ast TEXT
)
''')

# Create the users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    age INTEGER NOT NULL,
    department TEXT NOT NULL,
    salary INTEGER NOT NULL,
    experience INTEGER NOT NULL
)
''')

# Commit changes
conn.commit()

# Store user-defined functions
user_defined_functions = {}

# Function to define custom functions via API
def define_function(func_name, func_body):
    global user_defined_functions
    try:
        exec(func_body, {}, user_defined_functions)
        return f"Function '{func_name}' defined successfully!"
    except Exception as e:
        raise ValueError(f"Failed to define function '{func_name}': {e}")

# Function to convert Python AST into custom Node
def create_rule(rule_string):
    try:
        tree = ast.parse(rule_string, mode='eval')  # Parse rule string to AST
        return convert_ast(tree.body)  # Convert AST to custom Node structure
    except SyntaxError as e:
        raise ValueError(f"Invalid rule syntax: {e}")

# Convert parsed AST to custom Node structure
def convert_ast(py_ast):
    if isinstance(py_ast, ast.BoolOp):
        op = 'AND' if isinstance(py_ast.op, ast.And) else 'OR'
        return Node('operator', left=convert_ast(py_ast.values[0]), right=convert_ast(py_ast.values[1]), value=op)
    elif isinstance(py_ast, ast.Compare):
        left = py_ast.left.id
        comparator = py_ast.ops[0]
        if isinstance(comparator, ast.Gt):
            op = '>'
        elif isinstance(comparator, ast.Lt):
            op = '<'
        elif isinstance(comparator, ast.Eq):
            op = '=='
        right = py_ast.comparators[0].n
        return Node('operand', value=f"{left} {op} {right}")
    elif isinstance(py_ast, ast.Call):
        func_name = py_ast.func.id
        args = [convert_ast(arg) for arg in py_ast.args]
        return Node('function_call', func_name=func_name, args=args)

# Save rule to database
def save_rule_to_db(rule_string, rule_ast):
    rule_ast_json = json.dumps(rule_ast.__dict__, default=lambda o: o.__dict__)
    cursor.execute('''
    INSERT INTO rules (rule_string, rule_ast)
    VALUES (?, ?)
    ''', (rule_string, rule_ast_json))
    conn.commit()

# Save user to database
def save_user_to_db(age, department, salary, experience):
    cursor.execute('''
    INSERT INTO users (age, department, salary, experience)
    VALUES (?, ?, ?, ?)
    ''', (age, department, salary, experience))
    conn.commit()

# Retrieve rule by ID
def get_rule_by_id(rule_id):
    cursor.execute('SELECT rule_string, rule_ast FROM rules WHERE id = ?', (rule_id,))
    rule = cursor.fetchone()
    
    if rule:
        rule_string, rule_ast_json = rule
        rule_ast_dict = json.loads(rule_ast_json)
        
        def build_ast_from_dict(ast_dict):
            node = Node(ast_dict['type'], value=ast_dict.get('value'))
            if ast_dict.get('left'):
                node.left = build_ast_from_dict(ast_dict['left'])
            if ast_dict.get('right'):
                node.right = build_ast_from_dict(ast_dict['right'])
            return node
        
        rule_ast = build_ast_from_dict(rule_ast_dict)
        return rule_ast
    return None

# Retrieve user by ID
def get_user_by_id(user_id):
    cursor.execute('SELECT age, department, salary, experience FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if user:
        return {
            "age": user[0],
            "department": user[1],
            "salary": user[2],
            "experience": user[3]
        }
    return None

# Evaluate the rule using the node and user data
def evaluate_rule(node, user_data):
    if node.type == 'operand':
        attribute, operator, value = node.value.split()
        attribute_value = user_data.get(attribute)
        if operator == '>':
            return attribute_value > int(value)
        elif operator == '<':
            return attribute_value < int(value)
        elif operator == '==':
            return attribute_value == value
    elif node.type == 'operator':
        left_result = evaluate_rule(node.left, user_data)
        right_result = evaluate_rule(node.right, user_data)
        if node.value == 'AND':
            return left_result and right_result
        elif node.value == 'OR':
            return left_result or right_result
    elif node.type == 'function_call':
        func_name = node.func_name
        args = [evaluate_rule(arg, user_data) for arg in node.args]
        if func_name in user_defined_functions:
            return user_defined_functions[func_name](*args)
        else:
            raise ValueError(f"Undefined function '{func_name}'.")

# Flask application
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

# Add new rule to the system
@app.route('/add_rule', methods=['POST'])
def add_rule():
    rule_string = request.form['rule_string']
    try:
        rule_ast = create_rule(rule_string)
        save_rule_to_db(rule_string, rule_ast)
        return jsonify({"message": "Rule added successfully!"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

# Add a new user
@app.route('/add_user', methods=['POST'])
def add_user():
    try:
        age = int(request.form['age'])
        department = request.form['department']
        salary = int(request.form['salary'])
        experience = int(request.form['experience'])
        
        # Save user to the database
        save_user_to_db(age, department, salary, experience)
        return jsonify({"message": "User added successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Evaluate a user against a specific rule
@app.route('/evaluate_user', methods=['POST'])
def evaluate_user():
    user_data = {
        'age': int(request.form['age']),
        'department': request.form['department'],
        'salary': int(request.form['salary']),
        'experience': int(request.form['experience'])
    }
    rule_id = int(request.form['rule_id'])
    rule_ast = get_rule_by_id(rule_id)
    if rule_ast and user_data:
        result = evaluate_rule(rule_ast, user_data)
        return jsonify({"result": f"User matches rule: {result}"}), 200
    return jsonify({"error": "Invalid data."}), 400

# Define user functions via API
@app.route('/define_function', methods=['POST'])
def define_user_function():
    func_name = request.form['func_name']
    func_body = request.form['func_body']
    
    try:
        # Example of defining the function by adding to the dictionary
        define_function(func_name, func_body)
        return jsonify({"message": f"Function '{func_name}' defined successfully!"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
