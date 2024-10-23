import sqlite3
import json
import ast

# Define the Node class
class Node:
    def __init__(self, type, left=None, right=None, value=None):
        self.type = type
        self.left = left
        self.right = right
        self.value = value

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('rule_engine.db')
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

# Function to convert Python AST into custom Node
def create_rule(rule_string):
    try:
        tree = ast.parse(rule_string, mode='eval')  # Parse rule string to AST
        return convert_ast(tree.body)  # Convert AST to custom Node structure
    except SyntaxError:
        raise ValueError("Invalid rule syntax.")

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
    else:
        raise ValueError("Unsupported AST node type.")

def save_rule_to_db(rule_string, rule_ast):
    # Convert the AST to JSON for storage
    rule_ast_json = json.dumps(rule_ast.__dict__, default=lambda o: o.__dict__)

    cursor.execute('''
    INSERT INTO rules (rule_string, rule_ast)
    VALUES (?, ?)
    ''', (rule_string, rule_ast_json))
    
    conn.commit()

def save_user_to_db(age, department, salary, experience):
    cursor.execute('''
    INSERT INTO users (age, department, salary, experience)
    VALUES (?, ?, ?, ?)
    ''', (age, department, salary, experience))
    
    conn.commit()

def get_rule_by_id(rule_id):
    cursor.execute('SELECT rule_string, rule_ast FROM rules WHERE id = ?', (rule_id,))
    rule = cursor.fetchone()
    
    if rule:
        rule_string, rule_ast_json = rule
        # Deserialize the AST
        rule_ast_dict = json.loads(rule_ast_json)
        
        # Rebuild the AST from the JSON representation
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

def evaluate_rule(node, user_data):
    if node.type == 'operand':
        # Extract variable and comparison operator
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

# New function to combine multiple rules using 'OR'
def combine_rules(rules):
    combined_ast = None
    for rule_string in rules:
        try:
            rule_ast = create_rule(rule_string)
            if combined_ast:
                combined_ast = Node('operator', left=combined_ast, right=rule_ast, value='OR')
            else:
                combined_ast = rule_ast
        except ValueError as e:
            print(f"Skipping rule due to error: {e}")
    return combined_ast

# Example usage:
rule_string1 = "age > 30"
rule_string2 = "salary > 50000"

combined_ast = combine_rules([rule_string1, rule_string2])

save_user_to_db(32, "Sales", 60000, 3)

user_data = get_user_by_id(1)

if combined_ast and user_data:
    result = evaluate_rule(combined_ast, user_data)
    print(f"User matches combined rule: {result}")
else:
    print("No valid combined rule found.")
