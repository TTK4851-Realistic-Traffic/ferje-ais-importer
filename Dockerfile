# Use
FROM public.ecr.aws/lambda/python:3.8

COPY ferjeimporter/   ./
COPY ./requirements-frozen.txt ./requirements-frozen.txt

RUN pip3 install -r requirements-frozen.txt
CMD ["main.handler"]