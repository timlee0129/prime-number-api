FROM python:3.8.9

# Set working directory
WORKDIR /prime_number_project

# copy requirements file
COPY ./requirements.txt /prime_number_project/requirements.txt

# install dependencies
RUN pip install --no-cache-dir --upgrade -r /prime_number_project/requirements.txt

# copy code
COPY ./prime_number_api /prime_number_project/prime_number_api

# run app
CMD ["uvicorn", "prime_number_api.main:app", "--host", "0.0.0.0", "--port", "80"]
