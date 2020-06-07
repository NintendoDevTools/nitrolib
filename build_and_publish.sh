python setup.py sdist bdist_wheel
rm -rf build
twine upload dist/*
