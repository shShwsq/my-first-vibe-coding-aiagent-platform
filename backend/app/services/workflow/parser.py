import json
import logging
import re
import textwrap


logger = logging.getLogger(__name__)

class WorkflowParser:
    def __init__(self):
        self.nodes = {}
    
    def parse(self, workflow_text):
        logger.info("="*50)
        logger.info(f"Start parsing workflow text")
        
        try:
            workflow_text = self._remove_comments(workflow_text)
        except Exception as e:
            logger.error(f"Error removing comments: {e}")
            return {}
        try:
            nodes = self._split_statements(workflow_text)
            logger.info(f"Split nodes: {nodes}")
            self.nodes = nodes
        except Exception as e:
            logger.error(f"Error splitting statements: {e}")
            return {}
        
        return self.nodes
    

    def _remove_comments(self, text: str) -> str:
        result = []
        i = 0
        n = len(text)
        in_single_quote = False
        in_double_quote = False
        in_line_comment = False
        in_block_comment = False
        
        while i < n:
            ch = text[i]
            
            # 处理字符串字面量（防止字符串内的注释标记被误删）
            if not in_line_comment and not in_block_comment:
                if ch == "'" and (i == 0 or text[i-1] != '\\'):
                    in_single_quote = not in_single_quote
                elif ch == '"' and (i == 0 or text[i-1] != '\\'):
                    in_double_quote = not in_double_quote
            
            # 只在非字符串内检测注释
            if not (in_single_quote or in_double_quote):
                if not in_line_comment and not in_block_comment:
                    # 单行注释 //
                    if ch == '/' and i+1 < n and text[i+1] == '/':
                        in_line_comment = True
                        i += 1  # 跳过第二个 '/'
                        continue
                    if ch == '#': 
                        in_line_comment = True
                        continue
                    # 多行注释 /*
                    elif ch == '/' and i+1 < n and text[i+1] == '*':
                        in_block_comment = True
                        i += 1  # 跳过 '*'
                        continue
            
            # 处理注释结束
            if in_line_comment:
                if ch == '\n':
                    in_line_comment = False
                    result.append(ch)   # 保留换行符
                
                # 忽略其他注释字符
            elif in_block_comment:
                if ch == '*' and i+1 < n and text[i+1] == '/':
                    in_block_comment = False
                    i += 1  # 跳过 '/'
                # 忽略其他注释字符
            else:
                result.append(ch)
            
            i += 1
        
        return ''.join(result)


    
    def _split_statements(self, text):
        statements = {}
        current = []
        in_code_block = False
        code_block_delimiter = None
        current_node_id = 0
        in_json_string = False
        json_string_char = None
        brace_depth = 0

        for line in text.splitlines():
            stripped = line.strip()

            if not in_code_block and stripped in ('{', '```'):
                in_code_block = True
                code_block_delimiter = stripped
                continue

            if in_code_block:
                end_marker = '}' if code_block_delimiter == '{' else '```'
                if stripped == end_marker:
                    in_code_block = False
                    code_block_delimiter = None
                    block_content = '\n'.join(current)
                    dedented_block = textwrap.dedent(block_content)
                    if f"{current_node_id}_code" not in statements and dedented_block:
                        statements[f"{current_node_id}_code"] = dedented_block
                    else:
                        logger.warning(f"Duplicate code block for node {current_node_id}")
                    
                    current = []
                    continue

            if in_code_block:
                current.append(line)
                continue

            for char in line:
                if not in_json_string:
                    if char in '"\'':
                        in_json_string = True
                        json_string_char = char
                    elif char == '{':
                        brace_depth += 1
                    elif char == '}':
                        brace_depth -= 1
                    elif char == ';' and brace_depth == 0:
                        statement = ''.join(current)
                        clean_statement = re.sub(r'\s+', '', statement).rstrip(';')
                        search_pattern = r'"id":(.*?),' 
                        match = re.search(search_pattern, clean_statement)
                        if match:
                            current_node_id = str(match.group(1).strip('"').strip("'"))
                            processed_statement = self._preprocess_expressions(statement.rstrip(';'))
                            if f"{current_node_id}" not in statements and processed_statement:
                                statements[f"{current_node_id}"] = processed_statement
                            else:
                                logger.warning(f"Duplicate statement for node {current_node_id}")
                        else:
                            logger.warning(f"Statement {statement} does not contain 'id'.")
                        current = []
                        continue
                else:
                    if char == json_string_char and (len(current) == 0 or current[-1] != '\\'):
                        in_json_string = False
                        json_string_char = None
                current.append(char)

        if current:
            statement = ''.join(current)
            clean_statement = re.sub(r'\s+', '', statement).rstrip(';')
            search_pattern = r'"id":(.*?),' 
            match = re.search(search_pattern, clean_statement)
            if match:
                current_node_id = str(match.group(1).strip('"').strip("'"))
                processed_statement = self._preprocess_expressions(statement.rstrip(';'))
                if f"{current_node_id}" not in statements and processed_statement:
                    statements[f"{current_node_id}"] = processed_statement
                else:
                    logger.warning(f"Duplicate statement for node {current_node_id}")
            else:
                if statement:
                    logger.warning(f"Statement {statement} does not contain 'id'.")

        return statements

    def _preprocess_expressions(self, text):
        """
        预处理文本中的 Python 表达式，将其转换为带标记的字符串。
        支持的表达式类型：
        - ctx.xxx()
        - ctx.xxx.yyy (属性访问)
        - memory.xxx()
        
        处理两种场景：
        1. 字符串内的表达式：保持原样，后续在 executor 中处理
        2. 独立作为值的表达式：转换为 {"__expr__": "表达式"}
        """
        expr_pattern = r'(ctx\.\w+(?:\([^)]*\))?(?:\.\w+)*|memory\.\w+(?:\([^)]*\))?(?:\.\w+)*)'
        
        result = []
        i = 0
        in_string = False
        string_char = None
        
        while i < len(text):
            char = text[i]
            
            if char in '"\'':
                if not in_string:
                    in_string = True
                    string_char = char
                    result.append(char)
                    i += 1
                    continue
                elif char == string_char:
                    if i > 0 and text[i-1] == '\\':
                        result.append(char)
                        i += 1
                        continue
                    in_string = False
                    string_char = None
                    result.append(char)
                    i += 1
                    continue
            
            if in_string:
                result.append(char)
                i += 1
                continue
            
            remaining = text[i:]
            match = re.match(expr_pattern, remaining)
            
            if match:
                expr = match.group(1)
                result.append(json.dumps({"__expr__": expr}))
                i += len(expr)
            else:
                result.append(char)
                i += 1
        
        return ''.join(result)


    def validate(self,text):
        parsed_nodes = self.parse(text)
        start_node = parsed_nodes.get('start')
        if not start_node:
            return False, "缺少start节点", []
        else:
            len_nodes = len(parsed_nodes)
            logger.info(f"Total nodes: {len_nodes}")
            if len_nodes == 1:
                return False, "缺少非start节点", []     
            else:
                start_node_json = json.loads('{'+start_node+'}')
                if 'params' not in start_node_json:
                    return True, "验证通过", [{"name": "content", "type": "str"}]      
                else:
                    params = start_node_json['params']
                    return True, "验证通过", params



   