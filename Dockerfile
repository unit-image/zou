FROM python:2.7

EXPOSE 5000

# Install external dependencies
# We do it separatly to leverage docker build cache
WORKDIR zou
COPY setup.py setup.cfg ./
COPY zou/__init__.py ./zou/
RUN ls
RUN python -c "import distutils.core; setup = distutils.core.run_setup('setup.py'); print('\n'.join(setup.install_requires))" > image-requirements.txt
RUN cat image-requirements.txt
RUN pip install -r image-requirements.txt


# Install zou
COPY . .
RUN pip install -r requirements.txt