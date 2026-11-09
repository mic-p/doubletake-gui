"""Pure tests for argument validation without importing PySide6."""
import ast
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'app.py'
root = ast.parse(SOURCE.read_text(encoding='utf-8'))
function = next(node for node in root.body if isinstance(node, ast.FunctionDef)
                and node.name == 'validate_port_range')
module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
namespace = {'PORT_RANGE_RE': __import__('re').compile(r'^(\d{1,5})-(\d{1,5})$')}
exec(compile(module, str(SOURCE), 'exec'), namespace)
validate_port_range = namespace['validate_port_range']


class ValidationTests(unittest.TestCase):
    def test_empty_and_valid_ranges(self):
        for value in ('', '60000-60002', '1-3', '60000-60010'):
            validate_port_range(value)

    def test_invalid_ranges(self):
        for value in ('foo', '80', '5-3', '60000-60001', '0-3', '65534-65536'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_port_range(value)


if __name__ == '__main__':
    unittest.main()
