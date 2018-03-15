# Use base image
FROM etal/cnvkit:0.9.3

# File Author / Maintainer
LABEL Mantainer Juan S. Medina, Juan E. Arango <medinaj@mskcc.org>

# Define directories
ENV OUTPUT_DIR /data
ENV WORK_DIR /code
ENV OPT_DIR /opt
ENV SHARED_FS /ifs

# Install Dependencies
WORKDIR ${OPT_DIR}
RUN apt-get update && apt-get -yqq install \
        git \
        ghostscript \
        imagemagick \
        locales \
    \
    && git clone https://github.com/raphael-group/THetA.git \
    && git clone https://michaelchughes@bitbucket.org/michaelchughes/bnpy-dev/ \
    \
    # Configure default locale,
    && echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
    && locale-gen en_US.utf8 \
    && /usr/sbin/update-locale LANG=en_US.UTF-8

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
RUN pip install -r requirements.txt

# Run command
ENTRYPOINT ["toil_cnvkit"]



