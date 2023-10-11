FROM python:3.9 
# Or any preferred Python version.
WORKDIR /app
ADD *.py .
ADD requirements.txt .
RUN pip install -r requirements.txt
CMD [“python3”, “./background_tasks.py”] 
# Or enter the name of your unique directory and parameter set.