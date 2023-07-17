FROM jupyter/base-notebook:hub-3.0.0 as base

RUN pip install --upgrade pip

# from base notebook image
ARG NB_USER="jovyan"
ARG NB_UID="1000"
ARG NB_GID="100"

USER root

RUN mkdir /app
WORKDIR /app

RUN conda install -c conda-forge gxx jupyterlab ipywidgets gdal


# Create a duplicate in /app
COPY . /app

RUN pip install -e /app

RUN jupyter lab build --minimize=False /app

RUN chown -R ${NB_UID}:${NB_GID} /app
USER ${NB_UID}
