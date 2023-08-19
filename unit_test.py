import latex
import json
from unittest import TestCase
from util import open_file, save_file

class LatexTests(TestCase):
	def runTest(self):
		latex_file = 'test_latex.tex'
		file_data = open_file(latex_file)
		parser = latex.LatexParser(file_data)
		latex_data = parser.sections
		# save_file('latex.json', json.dumps(latex_data))
		idx = 0
		for section in latex_data:
			print(f'### {section.title}')
			for subsection in section.subsections:
				print(f'###### {subsection.title}\n{subsection.content}')
			if idx > 1:
				break
			idx += 1
		self.assertEqual(16, len(latex_data), 'Wrong number of sections')
		print('All tests passed!')

test = LatexTests()
test.runTest()