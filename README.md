genesisclient
=============

A Genesis (DeStatis et. al.) client for Python - in a very early stage.

The goal here is to create a tool that allows for automated lookup and download of resources from several official statistics offices in Germany.

Currently, downloading of tables in various formats works in many cases.

## Installation

Download or clone, change to the directory containing `setup.py` and execute

    python setup.py install
    pip install suds lxml

## Supported backends

The client needs configuration for the backend systems to work with. On the command line you reference the desired system using the `-s` parameter and the handle for that system (see below for examples).

* `DESTATIS`: [www-genesis.destatis.de](https://www-genesis.destatis.de/)
* `LDNRW`: [Landesdatenbank NRW](https://www.landesdatenbank.nrw.de/)
* `REGIONAL`: [regionalstatistik.de](https://www.regionalstatistik.de/)

You might need a user account (user name and password) for the system.

## Usage

### Quickstart

Download the table with reference code `13211-03ir` from the "Landesdatenbank NRW":

    python -m genesisclient -s LDNRW -d 13211-03ir

This writes a file `13211-03ir.csv` to your current working directory.

The DESTATIS system requires a login for all operations. In order to test downloading here, fill in your credentials in the command beow and execute it:

    python -m genesisclient -s DESTATIS -u YOUR_USERNAME -p YOUR_PASSWORD -d 14111-0001

### Specifying the output file format

The parameter `-f` allows you to chose betweet `csv` (default), `xls` and `html` output.

    python -m genesisclient -s LDNRW -d 13211-03ir -f xls

### Selecting data for a specific region

Genesis systems use a location hierarchy depending on which system you work with. When requesting a data table, by default, the data is not restricted to a specific region. When working with the DESTATIS system, this usually means you get data for entire Germany. When requesting a specific location, different data is contained in the response, usually matching the requested region.

Regions/locations are indicated using the "Amtlicher Gemeindeschlüssel". See https://github.com/marians/agssearch for a handy tool to find keys for location names. Note that you can omit trailing zeros.

This example shows how to download data from table `13211-03ir` for the City of Cologne:

    python -m genesisclient -s LDNRW -d 13211-03ir --rs 05315

