FROM python:3.7

EXPOSE 5000

# install pg_dump
RUN apt-get update && apt-get install postgresql-client --yes

# Install external dependencies
# We do it separatly to leverage docker build cache
WORKDIR /opt/zou
COPY setup.py setup.cfg ./
COPY zou/__init__.py ./zou/
RUN python -c "import distutils.core; setup = distutils.core.run_setup('setup.py'); print('\n'.join(setup.install_requires))" > image-requirements.txt
RUN pip install -r image-requirements.txt

# install ffmpeg
RUN apt-get install ffmpeg --yes

# Install zou
COPY . .
RUN pip install -r requirements.txt