
from typing import Dict

import yaml

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
