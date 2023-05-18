#!/usr/bin/env python

"""jga_metadata_import.py  :  Consumes the JGA API and import the study metadata from the Japanese Genome Archive. """

__author__ = "Mauricio Moldes"
__version__ = "0.1"
__maintainer__ = "Mauricio Moldes"
__email__ = "mauricio.moldes@crg.es"
__status__ = "development"

import json
import datetime
import logging
import psycopg2
import requests
import sys
import yaml

logger = logging.getLogger('jga_import_logger')

""" VERIFIES THE CONNECTION TO PLSQL """


def connection_plsql():
    conn_string = "host='" + str(cfg['plsql_staging']['host']) + "' dbname='" + str(
        cfg['plsql_staging']['dbname']) + "' user='" + str(
        cfg['plsql_staging']['user']) + "' password='" + str(cfg['plsql_staging']['password']) + "' port = '" + str(
        cfg['plsql_staging']['port']) + "'"
    conn_plsql = psycopg2.connect(conn_string)
    return conn_plsql


""" PARSES ATTRIBUTE """


def parse_target_attribute(response_info, attribute):
    try:
        result = response_info[attribute]
    except Exception as e:
        logger.error("Error: {}".format(e))
        result = None
    return result


""" PARSES NESTED ATTRIBUTES """


def parse_multiple_target_attribute(response_info, attribute):
    if attribute == "publications":
        try:
            publications = response_info['properties']['PUBLICATIONS']['PUBLICATION']
            result = publications
        except Exception as e:
            logger.error("Error: {}".format(e))
            result = None
    elif attribute == "study_type":
        try:
            study_types = response_info['properties']['DESCRIPTOR']['STUDY_TYPES']['STUDY_TYPE']
            result = study_types
        except Exception as e:
            logger.error("Error: {}".format(e))
            result = None
    elif attribute == "center_name":
        try:
            result = response_info['properties']['center_name']
        except Exception as e:
            logger.error("Error: {}".format(e))
            result = None
    elif attribute == "abstract":
        try:
            result = response_info['properties']['DESCRIPTOR']['STUDY_ABSTRACT']
        except Exception as e:
            logger.error("Error: {}".format(e))
            result = None

    return result


"""  """


def parse_studies_response(response_info):
    jga_studies = []
    results = response_info['dbXrefs']
    for result in results:
        type = result['type']
        if type == "jga-study":
            study_stable_id = result['identifier']
            jga_studies.append(study_stable_id)
    return jga_studies


""" ALL JGA STUDIES BELONG TO THE SAME DAC JGAC000001, QUERIES ALL STUDIES AND DATASETS LINKED TO THAT DAC """


def get_jga_studies():
    try:
        response = requests.get("https://ddbj.nig.ac.jp/resource/jga-dac/JGAC000001.json", timeout=30)
        response.raise_for_status()
        # Code here will only run if the request is successful
        response_info = response.json()
        return response_info
    except requests.exceptions.HTTPError as errh:
        return errh
    except requests.exceptions.ConnectionError as errc:
        return errc
    except requests.exceptions.Timeout as errt:
        return errt
    except requests.exceptions.RequestException as err:
        return err


""" CONVERTS DICT to JSON """


def convert_dict_to_json(list):
    result = json.dumps(list)
    return result


""" SELECTED ATRIBUTES FOR THE IMPORT OF JGA  """


def parse_target_study(response_info):
    repository = parse_target_attribute(response_info, 'isPartOf')
    identifier = parse_target_attribute(response_info, 'identifier')
    title = parse_target_attribute(response_info, 'title')
    description = parse_target_attribute(response_info, 'description')
    status = parse_target_attribute(response_info, 'status')
    visibility = parse_target_attribute(response_info, 'visibility')
    date_created = parse_target_attribute(response_info, 'dateCreated')
    date_published = parse_target_attribute(response_info, 'datePublished')
    date_modified = parse_target_attribute(response_info, 'dateModified')
    alias = parse_target_attribute(response_info, 'name')
    dbxrefs = parse_target_attribute(response_info, 'dbXrefs')
    dbxrefs_json = convert_dict_to_json(dbxrefs)
    abstract = parse_multiple_target_attribute(response_info, 'abstract')
    center_name = parse_multiple_target_attribute(response_info, 'center_name')
    publications = parse_multiple_target_attribute(response_info, 'publications')
    publications_json = convert_dict_to_json(publications)
    study_type = parse_multiple_target_attribute(response_info, 'study_type')
    study_type_json = convert_dict_to_json(study_type)

    return identifier, title, description, status, visibility, repository, publications_json, study_type_json, alias, dbxrefs_json, abstract, center_name, date_created, date_modified, date_published


""" SCRAPES ATTRIBUTES FOR EACH STUDY PAGE """


def get_study(study):
    try:
        response = requests.get("https://ddbj.nig.ac.jp/resource/jga-study/" + study + ".json", timeout=5)
        response.raise_for_status()
        # Code here will only run if the request is successful
        response_info = response.json()
        return response_info
    except requests.exceptions.HTTPError as errh:
        return errh
    except requests.exceptions.ConnectionError as errc:
        return errc
    except requests.exceptions.Timeout as errt:
        return errt
    except requests.exceptions.RequestException as err:
        return err


""" INSERTS STUDY IN DB  """


def insert_jga_studies(conn_plsql, identifier, title, description, status, visibility,
                       repository, publications, study_type, alias, dbxrefs, abstract, center_name,
                       date_created, date_modified, date_published):
    cursor = conn_plsql.cursor()
    sql = " INSERT INTO jga_study_table (\"id\", jga_stable_id,title, description,  status, visibility, repository, publications, study_type, alias, dbxrefs, abstract, center_name,date_created,date_modified,date_published,created_at,edited_at,created_by_db_user,edited_by_db_user) " \
          " VALUES ( DEFAULT ," \
          " %s ," \
          " %s ," \
          " %s ," \
          " %s ," \
          " %s ," \
          " %s ," \
          " %s ," \
          " %s ," \
          " %s ," \
          " %s ," \
          " %s ," \
          " %s ," \
          " %s ," \
          " %s ," \
          " %s ," \
          "  DEFAULT," \
          "  DEFAULT," \
          "  DEFAULT," \
          "  DEFAULT)"

    cursor.execute(sql, (
        identifier, title, description, status, visibility, repository, publications, study_type, alias, dbxrefs,
        abstract, center_name, date_created,
        date_modified, date_published))
    conn_plsql.commit()
    cursor.close()


""" QUERY JGA STUDIES FROM DB  """


def query_jga_studies(conn_egaprod_stg_dev):
    results = []
    cursor = conn_egaprod_stg_dev.cursor()
    cursor.execute("SELECT \
                       jga_study_table.jga_stable_id \
                       FROM \
                       jga_study_table ;")
    records = cursor.fetchall()
    for record in records:
        results.append(record[0])
    return results


""" READ CONFIG FILE """


def read_config():
    with open("./config/config.yml", 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    return cfg


""" MAIN FUNCTION  """


def import_jga():
    logger.info("Process Started")
    removed_studies = ["JGAS00000000025",
                       "JGAS00000000054"]  # these two studies have been tagged has test in production so they will be removed
    conn_plsql = None
    try:
        print("bfore conn")
        conn_plsql = connection_plsql()
        print ("after conn")
        if conn_plsql:
            previous_studies = query_jga_studies(conn_plsql)  # obtains the existing list of studies
            response_info = get_jga_studies()
            jga_study_list_temp = parse_studies_response(response_info)
            jga_study_list = list(set(jga_study_list_temp) - set(removed_studies))
            previous_studies_len = len(previous_studies)  # existing study list
            jga_study_list_len = len(jga_study_list)  # new study list
            if previous_studies_len == jga_study_list_len:  # no updates required
                logger.info("No Update Required")
                logger.info("Process Ended")
                conn_plsql.close()
            else:
                set_previous_studies = set(previous_studies)
                set_jga_study_list = set(jga_study_list)
                mismatch = set_jga_study_list.symmetric_difference(set_previous_studies)
                for jga_study in mismatch:
                    try:
                        print(jga_study)
                        response_info = get_study(jga_study)
                        identifier, title, description, status, visibility, repository, publications, study_type, alias, dbxrefs, abstract, center_name, date_created, date_modified, date_published = parse_target_study(
                            response_info)
                        insert_jga_studies(conn_plsql, identifier, title, description, status,
                                           visibility, repository, publications, study_type, alias, dbxrefs, abstract,
                                           center_name, date_created,
                                           date_modified,
                                           date_published)  # inserts study in DB
                    except Exception as e:
                        logger.error("Error: {}".format(e))
    except Exception as e:
        logger.error("Error: {}".format(e))
    finally:
        if conn_plsql:
            conn_plsql.close()
            logger.debug("PLSQL connection closed")


""" MAIN"""


def main():
    try:
        print ("Queue music")
        # configure logging
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s [in %(pathname)s:%(lineno)d]'
        logging.basicConfig(format=log_format)
        global cfg
        cfg = read_config()
        import_jga()
    except Exception as e:
        logger.error("Error: {}".format(e))
        sys.exit(-1)


if __name__ == '__main__':
    main()
