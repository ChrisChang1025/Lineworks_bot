FROM python:3.11.6
WORKDIR /LineWorks

ADD . /LineWorks

RUN pip3 install -r ./requirements.txt
EXPOSE 9000
# ENTRYPOINT ["python3"]
# CMD ["flask_app.py"]
WORKDIR .
ENTRYPOINT ["python3", "LineWorks/flask_app.py"]
