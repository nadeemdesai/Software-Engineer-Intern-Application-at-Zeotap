import unittest
from rule_engine1 import create_rule, combine_rules, evaluate_rule, Node

class TestRuleEngine(unittest.TestCase):

    def test_create_rule(self):
        rule_string = "age > 30 and salary > 50000"
        rule_ast = create_rule(rule_string)
        self.assertIsInstance(rule_ast, Node)

    def test_combine_rules(self):
        rule1 = "age > 30 and salary > 50000"
        rule2 = "experience > 5 or department == 'Sales'"
        combined_ast = combine_rules([rule1, rule2])
        self.assertIsInstance(combined_ast, Node)

    def test_evaluate_rule(self):
        rule1 = "age > 30 and salary > 50000"
        rule2 = "experience > 5 or department == 'Sales'"
        combined_ast = combine_rules([rule1, rule2])
        
        user_data = {
            "age": 32,
            "salary": 60000,
            "experience": 3,
            "department": "Marketing"
        }
        result = evaluate_rule(combined_ast, user_data)
        self.assertTrue(result)

        # Test user data that doesn't match the rule
        user_data_invalid = {
            "age": 25,
            "salary": 40000,
            "experience": 1,
            "department": "Engineering"
        }
        result = evaluate_rule(combined_ast, user_data_invalid)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
