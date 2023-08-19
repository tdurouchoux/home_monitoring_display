from pathlib import Path
from typing import Dict, Literal

import yaml

class PathError(Exception):
    def __init__(self, path: Path, path_type: Literal["directory", "file"]) -> None:
        self.message = f"Missing corresponding {path_type} at location {path}"

def load_config(config_file: str) -> Dict:

    def math_op(loader, node):
        seq = loader.construct_sequence(node)
        
        if len(seq) > 2:
            raise ValueError(f'''Maths operation should take the following format: [operator, number]
                              (operator should be in ["+", "-", "/", "*"])
                              Got this sequence: {seq}''')
        
        if seq[0] == "+":
            return (lambda x: x + seq[1])
        elif seq[0] == "-":
            return (lambda x: x + seq[1])
        elif seq[0] == "/":
            return (lambda x: x / seq[1])
        elif seq[0] == "*":
            return (lambda x: x * seq[1])
        else:
            raise ValueError(f'''Operator should be in ["+", "-", "/", "*"])
                               Received following operator: {seq[0]}''')
    
    loader = yaml.SafeLoader

    loader.add_constructor("!math_op", math_op)

    with open(config_file, "r") as f:
        config = yaml.load(f, Loader=loader)

    return config

def extract_configs(conf_directory: Path, *conf_files: str) -> Dict:
    if not conf_directory.exists():
        raise PathError(conf_directory, "directory")
    
    conf = {}
    
    for conf_file in conf_files:
        conf_path = conf_directory / conf_file
        if not conf_path.exists():
            raise PathError(conf_path, "file")
        conf[conf_file] = load_config(conf_path)
    
    return conf