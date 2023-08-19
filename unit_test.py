import latex
import json
from unittest import TestCase
from util import open_file, save_file

class LatexTests(TestCase):
	def runTest(self):
		latex_file = 'test_latex.tex'
		file_data = open_file(latex_file)
		parser = latex.LatexParser(file_data)
		latex_data = parser.to_json()
		save_file('latex.json', json.dumps(latex_data))
		self.assertEqual(17, len(latex_data), 'Wrong number of sections')
		print('All tests passed!')

test = LatexTests()
test.runTest()