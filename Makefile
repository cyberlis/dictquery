clean:
	find . -name "*.pyc" | xargs rm -rf
	find . -name "__pycache__" | xargs rm -rf
	rm -f pep8.log
	rm -f pyflakes.log
	rm -f pylint.log
	rm -f sloccount.sc
	rm -f output.xml
	rm -f coverage.xml
	rm -f xunit*.xml
	rm -rf cover

init:
	python3 -m pip install -r requirements.txt

test:
	python3 -m unittest -v

