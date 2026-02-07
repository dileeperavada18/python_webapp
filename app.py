from flask import Flask, render_template, request, jsonify
import ast

app = Flask(__name__)

# White-listed methods to ensure security and functionality
ALLOWED_METHODS = {
    "list": ["append", "extend", "insert", "remove", "pop", "reverse", "sort"],
    "set": ["add", "update", "remove", "discard", "pop", "union", "intersection", "difference"],
    "tuple": ["count", "index"]
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run-operation', methods=['POST'])
def run_operation():
    try:
        data = request.json
        data_type = data.get('type') # 'list' or 'set'
        raw_input = data.get('input_data')
        method_name = data.get('method')
        args_raw = data.get('args', "")

        # 1. Safely parse the input string into a Python object
        # ast.literal_eval is safer than eval()
        obj = ast.literal_eval(raw_input)

        if data_type == "list" and not isinstance(obj, list):
            return jsonify({"error": "Input must be a valid list: [1, 2, 3]"}), 400
        if data_type == "set" and not isinstance(obj, (set, list)): # sets often come in as lists via JSON
            obj = set(obj)
        if data_type == "tuple":
            if not isinstance(obj, tuple):
                # Convert list-style input [1,2] to (1,2) if user types it wrong
                obj = tuple(ast.literal_eval(raw_input))
        elif data_type == "set":
            obj = set(obj)

        if method_name not in ALLOWED_METHODS[data_type]:
            return jsonify({"error": "Invalid method selected"}), 400

        # 2. Parse arguments
        # We split by comma for methods like .insert(index, obj)
        processed_args = []
        if args_raw:
            # Try to evaluate args as python objects (numbers, strings)
            for arg in args_raw.split(','):
                try:
                    processed_args.append(ast.literal_eval(arg.strip()))
                except:
                    processed_args.append(arg.strip())

        # 3. Execute the method
        # Most list/set methods modify in-place and return None
        method = getattr(obj, method_name)
        
        # Result of the operation (e.g., .pop() returns an item, .union() returns a new set)
        op_return = method(*processed_args)
        
        # For sets, we convert to list for JSON serialization
        display_result = list(obj) if data_type == "set" else obj

        return jsonify({
            "original": raw_input,
            "operation": f".{method_name}({args_raw})",
            "result": str(obj) if data_type == "list" else str(set(display_result)),
            "returned": str(op_return) if op_return is not None else "None (Modified In-Place)"
        })

    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 400

if __name__ == '__main__':
    app.run(debug=True)