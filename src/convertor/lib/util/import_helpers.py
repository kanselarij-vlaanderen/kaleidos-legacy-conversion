#!/usr/bin/python3

import csv
import os
import readline
import datetime
from pprint import pformat
import logging

def rlinput(prompt, prefill=''): # https://stackoverflow.com/a/2533142
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()

def manually_resolve(value, transformer, unresolved_value=None):
    while True:
        resolved_value = rlinput("Manually resolve: ", prefill=value)
        if resolved_value == value:
            return unresolved_value
        try:
            return transformer(resolved_value)
        except Exception as e:
            continue

def multiple_dict_diff(dicts):
    diffkeys = []
    for i in range(len(dicts)-1):
        for key in dicts[i]:
            if (dicts[i][key] != dicts[i+1][key]) and (key not in diffkeys):
                diffkeys.append(key)
    return tuple(diffkeys)


def import_csv(path, encoding='utf-8', custom_trans={}):
    dir, file = os.path.split(path)
    name, ext = os.path.splitext(file)
    writefile = name + '_errata_' + str(int(datetime.datetime.now().timestamp())) + ext
    write_path = os.path.join(dir, writefile)
    with open(path, encoding=encoding) as csvfile, open(write_path, 'w') as csvfile_write:
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(0)
        reader = csv.DictReader(csvfile, dialect=dialect)
        writer = csv.DictWriter(csvfile_write, fieldnames=reader.fieldnames)
        writer.writeheader()
        result = []
        n = 0
        for row in reader:
            n += 1
            breaker = False
            row_result = {}
            for key, value in row.items():
                if key in custom_trans:
                    try:
                        res = custom_trans[key]['parser'](value.strip())
                        row_result[key] = {'parsed': res, 'source': value, 'success': True}
                    except Exception as e:
                        row_result[key] = {'source': value, 'success': False}
                        if custom_trans[key]['required']:
                            logging.warning("Failed parsing required field \'{}\' with value \'{}\': {}, skipping line {}".format(key, value, e, n))
                            writer.writerow(row)
                            breaker = True
                            break
                        else:
                            logstring = "Failed parsing field \'{}\' with value \'{}\' on line {}".format(key, value, n)
                            if value:
                                logging.info(logstring)
                            else:
                                logging.debug(logstring)
                            

                else:
                    row_result[key] = {'parsed': value, 'source': value, 'success': True}
            if breaker: # skip rows with a field that doesn't parse
                continue
            else:
                result.append(row_result)
                logging.debug("{}: successfully parsed line {}:\n{}".format(file, n, pformat(row_result)))
        logging.info("{}: sucessfully parsed {} out of {} lines ({:.1f}%)".format(path, len(result), n, len(result)/n*100))
    return result
