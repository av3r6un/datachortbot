import ast
import operator

class SafeEval:
  ALLOWED_NODES = {
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod,
    ast.Pow, ast.USub, ast.UAdd, ast.Constant,
    ast.Call, ast.Name
  }
  
  SAFE_FUNCTIONS = {
    "max": max,
    "min": min,
    "abs": abs,
    "round": round
  }

  @staticmethod
  def eval(expr: str, variables: dict) -> float:
    tree = ast.parse(expr, mode="eval")

    for node in ast.walk(tree):
      if type(node) not in SafeEval.ALLOWED_NODES:
        raise ValueError("Unsafe expression")

    return SafeEval._eval_node(tree.body, variables)

  @staticmethod
  def _eval_node(node, variables):
    if isinstance(node, ast.Num):
      return node.n

    if isinstance(node, ast.Constant):
      return node.value

    if isinstance(node, ast.Name):
      return variables[node.id]

    if isinstance(node, ast.BinOp):
      left = SafeEval._eval_node(node.left, variables)
      right = SafeEval._eval_node(node.right, variables)

      op = node.op
      if isinstance(op, ast.Add):
        return left + right
      if isinstance(op, ast.Sub):
        return left - right
      if isinstance(op, ast.Mult):
        return left * right
      if isinstance(op, ast.Div):
        return left / right
      if isinstance(op, ast.Mod):
        return left % right
      if isinstance(op, ast.Pow):
        return left ** right

    if isinstance(node, ast.UnaryOp):
      operand = SafeEval._eval_node(node.operand, variables)
      if isinstance(node.op, ast.UAdd):
        return +operand
      if isinstance(node.op, ast.USub):
        return -operand

    if isinstance(node, ast.Call):
      func_name = node.func.id
      if func_name not in SafeEval.SAFE_FUNCTIONS:
        raise ValueError("Unsafe function")
      args = [SafeEval._eval_node(a, variables) for a in node.args]
      return SafeEval.SAFE_FUNCTIONS[func_name](*args)

    raise ValueError("Unsupported syntax")
