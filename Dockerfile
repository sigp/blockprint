FROM python:3.9
# Or any preferred Python version.
WORKDIR /app
COPY ./*.py .
ADD requirements.txt .
RUN pip install -r requirements.txt
# Or enter the name of your unique directory and parameter set.