FROM python:3.7-alpine3.9

RUN python -m pip install Pypdf2
RUN python -m pip install pytz
RUN python -m pip install python-dateutil

RUN mkdir /app
COPY extractor.py /app
RUN chmod +x /app/extractor.py

RUN ls /app
ENTRYPOINT ["python", "/app/extractor.py"]