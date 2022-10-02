import re
import sys
import ast
import os.path


class Message:
    def __init__(self, file_path, error_code, line_num, info):
        self.file_path = file_path
        self.error_code = error_code
        self.line_num = line_num
        self.info = info

    def __str__(self):
        return f"{self.file_path}: Line {self.line_num}: {self.error_code} {self.info}"


def is_snakecase(text: str) -> bool:
    for ch in text:
        if ch.isupper():
            return False
    return True


class FileValidator:
    def __init__(self, file_path):
        self.path = file_path
        self.message_box = []
        self.consecutive_blanklines = 0
        # validate the lines
        with open(file_path, 'r') as f:
            lines = f.readlines()
            for (i, line) in enumerate(lines):
                self.validate_line(i + 1, line)
        # validate the file
        with open(file_path, 'r') as f:
            file = f.read()
            self.validate_ast(ast.parse(file))

    def print_messages(self):
        self.message_box.sort(key=lambda msg: (msg.line_num, msg.error_code))
        for message in self.message_box:
            print(message)

    def validate_line(self, line_num, text):
        if len(text.strip()) == 0:
            self.consecutive_blanklines += 1
            return
        self.s001(line_num, text)
        self.s002(line_num, text)
        self.s003(line_num, text)
        self.s004(line_num, text)
        self.s005(line_num, text)
        self.s006(line_num, text)
        self.s007(line_num, text)
        self.consecutive_blanklines = 0

    # check file length
    def s001(self, line_num, text):
        if len(text) >= 80:
            self.message_box.append(Message(self.path, 'S001', line_num, 'Too long'))

    # check white spaces
    def s002(self, line_num, text):
        spaces = 0
        for j in range(0, len(text)):
            if text[j] == ' ':
                spaces += 1
            else:
                break
        if spaces % 4 != 0:
            self.message_box.append(Message(self.path, 'S002', line_num, 'Indentation is not a multiple of four'))

    # check semicolon in statements
    def s003(self, line_num, text):
        single_quotes = 0
        double_quotes = 0
        for j in range(0, len(text)):
            if text[j] == "'":
                single_quotes += 1
                continue
            if text[j] == '"':
                double_quotes += 1
                continue
            if text[j] == '#':
                return
            if text[j] == ';' and (single_quotes % 2 == 0) and (double_quotes % 2 == 0):
                self.message_box.append(Message(self.path, 'S003', line_num, 'Unnecessary semicolon'))
                return

    # check inline comments
    def s004(self, line_num, text):
        if text.strip()[0] == '#':
            return

        consecutive_spaces = 0
        for j in range(0, len(text)):
            if text[j] == ' ':
                consecutive_spaces += 1
            else:
                if text[j] == '#':
                    if consecutive_spaces < 2:
                        self.message_box.append(Message(self.path, 'S004', line_num,
                                                        'At least two spaces required before inline comments'))
                    return
                else:
                    consecutive_spaces = 0

    # check todos in comments
    def s005(self, line_num, text):
        if '#' in text:
            str_list = re.split('#', text, maxsplit=1)
            if 'todo' in str_list[1].lower():
                self.message_box.append(Message(self.path, 'S005', line_num, 'TODO found'))

    # check consecutive white lines before a code line
    def s006(self, line_num, text):
        if text.strip()[0] != '#' and self.consecutive_blanklines > 2:
            self.message_box.append(Message(self.path, 'S006', line_num,
                                            'More than two blank lines used before this line'))

    # check white spaces after class
    def s007(self, line_num, text):
        if 'class' in text:
            name = re.split('class', text, maxsplit=1)[1]
            spaces = 0
            for j in range(0, len(name)):
                if name[j] == ' ':
                    spaces += 1
                else:
                    break
            if spaces != 1:
                self.message_box.append(Message(self.path, 'S007', line_num, "Too many spaces after 'class'"))
        elif 'def' in text:
            name = re.split('def', text, maxsplit=1)[1]
            spaces = 0
            for j in range(0, len(name)):
                if name[j] == ' ':
                    spaces += 1
                else:
                    break
            if spaces != 1:
                self.message_box.append(Message(self.path, 'S007', line_num, "Too many spaces after 'def'"))

    def validate_ast(self, tree):
        for node in ast.walk(tree):
            # self.s008(tree)  # check if class name follows CamelCase
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                if class_name[0].islower():
                    self.message_box.append(Message(self.path, 'S008', node.lineno,
                                                    f"Class name '{class_name}' should use CamelCase"))
            # self.s009(tree)  # check if function name follows snake_case
            elif isinstance(node, ast.FunctionDef):
                function_name = node.name
                if not is_snakecase(function_name):
                    self.message_box.append(Message(self.path, 'S009', node.lineno,
                                                    f"Function name '{function_name}' should use snake_case"))
                # self.s010(tree)  # check if argument name follows snake_case
                arguments = [a.arg for a in node.args.args]
                for arg in arguments:
                    if not is_snakecase(arg):
                        self.message_box.append(Message(self.path, 'S010', node.lineno,
                                                        f"Argument name '{arg}' should use snake_case"))
                        break
                # self.s012(tree)  # check if default argument is mutable
                kw_default = node.args.defaults
                for default in kw_default:
                    if isinstance(default, ast.List)\
                            or isinstance(default, ast.Set)\
                            or isinstance(default, ast.Dict):
                        self.message_box.append(Message(self.path, 'S012', node.lineno,
                                                        f"Default argument(s) should not be mutable"))
                        break
            # self.s011(tree)   # check if variable name follows snake_case
            elif isinstance(node, ast.Assign):
                for e in node.targets:
                    if isinstance(e, ast.Name):
                        variable_name = e.id
                        if not is_snakecase(variable_name):
                            self.message_box.append(Message(self.path, "S011", node.lineno,
                                                    f"Variable name {variable_name} should use snake_case"))


def validate_file(file_path):
    validator = FileValidator(file_path)
    validator.print_messages()


args = sys.argv
path = args[1]


if os.path.isdir(path):
    for x in os.listdir(path):
        new_path = f"{path}\\{x}"
        validate_file(new_path)
elif os.path.isfile(path):
    validate_file(path)
