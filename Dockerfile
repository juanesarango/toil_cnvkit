# Use base image
FROM  python:2.7-jessie

# File Author / Maintainer
LABEL Mantainer Juan S. Medina, Juan E. Arango <medinaj@mskcc.org>

# Define directories
ENV OUTPUT_DIR /data
ENV WORK_DIR /code
ENV OPT_DIR /opt
ENV SHARED_FS /ifs

# Install dependencies
COPY ./build/install_dependencies.sh /tmp
RUN bash /tmp/install_dependencies.sh

# Set paths for installed dependencies
ENV PATH ${OPT_DIR}/THetA/python:${PATH}
ENV PYTHONPATH ${OPT_DIR}/bnpy-dev:${PYTHONPATH}

# Set locales
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8

# Mount the output volume as persistant
VOLUME ${OUTPUT_DIR}
VOLUME ${SHARED_FS}

# Install toil_cnvkit
COPY . ${WORK_DIR}
WORKDIR ${WORK_DIR}
RUN pip install .

# Run command
ENTRYPOINT ["toil_cnvkit"]
