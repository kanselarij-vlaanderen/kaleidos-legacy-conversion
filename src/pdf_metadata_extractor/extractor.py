#!/usr/bin/python3

import csv
from copy import deepcopy
import datetime
from dateutil.tz import tzutc, tzoffset
import os
import re
import sys

import PyPDF2
from pytz import timezone

TIMEZONE = timezone('Europe/Brussels')

# Adapted from https://www.blog.pythonlibrary.org/2018/04/10/extracting-pdf-metadata-and-text-with-python/
def get_info(path):
    with open(path, 'rb') as f:
        pdf = PyPDF2.PdfFileReader(f)
        info = pdf.getDocumentInfo()
        number_of_pages = pdf.getNumPages()

    return info

# Adapted from https://stackoverflow.com/a/26796646
PDF_DATE_PATTERN = re.compile(''.join([
    r"^",
    r"(D:)?",
    r"(?P<year>\d\d\d\d)",
    r"(?P<month>\d\d)?",
    r"(?P<day>\d\d)?",
    r"(?P<hour>\d\d)?",
    r"(?P<minute>\d\d)?",
    r"(?P<second>\d\d)?",
    r"((?P<tz_utc>[zZ])|((?P<tz_offset>[+-])((?P<tz_hour>\d\d)')((?P<tz_minute>\d\d)')?))?",
    r"$"]))

def transform_date(date_str, default_tz=None):
    """
    Convert a pdf date such as "D:20120321183444+07'00'" into a usable datetime
    http://www.verypdf.com/pdfinfoeditor/pdf-date-format.htm
    (D:YYYYMMDDHHmmSSOHH'mm')
    :param date_str: pdf date string
    :return: datetime object
    """
    global PDF_DATE_PATTERN
    match = re.match(PDF_DATE_PATTERN, date_str)
    if match:
        date_info = match.groupdict()

        for k, v in date_info.items():  # transform values
            if k in ('year', 'month', 'day', 'hour', 'minute', 'second', 'tz_hour', 'tz_minute'):
                if v is None: # Defaults
                    if k in ('month', 'day'):
                        date_info[k] = 1
                    elif k in ('hour', 'minute', 'second', 'tz_hour', 'tz_minute'):
                        date_info[k] = 0
                else:
                    date_info[k] = int(v)

        if date_info['tz_utc']: # UTC
            date_info['tzinfo'] = tzutc()
        elif date_info['tz_offset'] is None:
            date_info['tzinfo'] = default_tz
        else:
            multiplier = 1 if date_info['tz_offset'] == '+' else -1
            date_info['tzinfo'] = tzoffset(None, multiplier*(3600 * date_info['tz_hour'] + 60 * date_info['tz_minute']))
        for k in ('tz_utc', 'tz_offset', 'tz_hour', 'tz_minute'):  # no longer needed
            del date_info[k]

        return datetime.datetime(**date_info)
    else:
        print('WARNING: unrecognised pdf date format: {}'.format(date_str))
        return None

if __name__ == '__main__':

    directory = sys.argv[1]
    directory_encoded = os.fsencode(directory)
    filepath_write = sys.argv[2]

    with open(filepath_write, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['filename', 'filesize', 'creation_date', 'modified_date'])
        writer.writeheader()
        for file in os.listdir(directory_encoded):
            filename = os.fsdecode(file)
            if filename.endswith(".pdf"):
                filepath = os.path.join(directory, filename)
                filesize = os.path.getsize(filepath)
                data = {'filename': filename, 'filesize': filesize}
                try:
                    info = get_info(filepath)
                    try:
                        creation_date = transform_date(info['/CreationDate'].strip())
                        if creation_date:
                            isoformat = creation_date.isoformat().replace('+00:00', 'Z')
                            print('{}: {} -> {}'.format(filename, info['/CreationDate'], isoformat))
                            data['creation_date'] = isoformat
                        else:
                            pass
                    except (TypeError, KeyError) as e:
                        print("{}: WARNING: {}".format(data['filename'], str(e)))
                        pass
                    try:
                        modified_date = transform_date(info['/ModDate'].strip())
                        if modified_date:
                            isoformat = modified_date.isoformat().replace('+00:00', 'Z')
                            print('{}: {} -> {}'.format(filename, info['/ModDate'], isoformat))
                            data['modified_date'] = isoformat
                        else:
                            pass
                    except (TypeError, KeyError) as e:
                        print("{}: WARNING: {}".format(data['filename'], str(e)))
                        pass
                except Exception as e: # Weird stuff happens when reading a file trough PyPDF2 now and then
                    print("{}: WARNING: {}".format(data['filename'], str(e)))
                    pass
                writer.writerow(data)
            else:
                continue
