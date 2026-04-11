import ast
import os
from dataclasses import dataclass
from typing import List


@dataclass
class CodeChunk:
    file_path:   str
    chunk_type:  str    # function / class / module
    chunk_name:  str
    content:     str
    start_line:  int
    end_line:    int


def chunk_python_file(file_path: str, source_code: str) -> List[CodeChunk]:
    '''
    Parses a Python file using AST and splits into
    function/class level chunks.
    '''
    chunks = []

    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        # If file has syntax errors, treat whole file as one chunk
        return [CodeChunk(
            file_path  = file_path,
            chunk_type = 'module',
            chunk_name = os.path.basename(file_path),
            content    = source_code,
            start_line = 1,
            end_line   = len(source_code.splitlines())
        )]

    lines = source_code.splitlines()

    for node in ast.walk(tree):
        # Extract functions
        if isinstance(node, ast.FunctionDef):
            start = node.lineno - 1
            end   = node.end_lineno
            chunks.append(CodeChunk(
                file_path  = file_path,
                chunk_type = 'function',
                chunk_name = node.name,
                content    = '\n'.join(lines[start:end]),
                start_line = node.lineno,
                end_line   = node.end_lineno
            ))

        # Extract classes
        elif isinstance(node, ast.ClassDef):
            start = node.lineno - 1
            end   = node.end_lineno
            chunks.append(CodeChunk(
                file_path  = file_path,
                chunk_type = 'class',
                chunk_name = node.name,
                content    = '\n'.join(lines[start:end]),
                start_line = node.lineno,
                end_line   = node.end_lineno
            ))

    # If no functions/classes found, add whole file as module chunk
    if not chunks:
        chunks.append(CodeChunk(
            file_path  = file_path,
            chunk_type = 'module',
            chunk_name = os.path.basename(file_path),
            content    = source_code,
            start_line = 1,
            end_line   = len(lines)
        ))

    return chunks


def chunk_repository(repo_path: str) -> List[CodeChunk]:
    '''
    Walks entire repo and chunks all Python files.
    Skips venv, pycache, migrations.
    '''
    all_chunks = []
    skip_dirs  = {'.git', '__pycache__', 'venv', 'migrations', 'node_modules'}

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for file in files:
            if not file.endswith('.py'):
                continue

            full_path = os.path.join(root, file)
            rel_path  = os.path.relpath(full_path, repo_path)

            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    source = f.read()

                if source.strip():
                    chunks = chunk_python_file(rel_path, source)
                    all_chunks.extend(chunks)
            except Exception:
                continue

    return all_chunks
