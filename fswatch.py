#!/usr/local/bin/python3
from collections import OrderedDict
import configparser
from datetime import datetime as dt
import ftplib
import json
import os
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from orgtools import get_org_table_as_json

# TODO: consider using a virtualenv

# get environment variables from cfg files, to simplify daemon configuration
Config = configparser.ConfigParser()
cwd = os.path.dirname(os.path.realpath(__file__))
Config.read([cwd + '/work-macbook.cfg', os.path.expanduser('~') + '/website.cfg'])
DROPBOX = Config.get('local', 'DROPBOX')
SYNC = Config.get('local', 'SYNC')

input_path = DROPBOX + '/txt'
local_path = SYNC + '/webmirror'
server_url = Config.get('website', 'URL')
user = Config.get('website', 'FTP_USERNAME')
password = Config.get('website', 'FTP_PASSWORD')
ignore_list = ['.DS_Store', '.git']  # ignore by simple substring match


def process_org_table(fin, fout, table_name, columns=None, rowfunc=None):
    """
    given input and output filenames, and a table name,
    read org table in input file, convert to json, and write to output file
    - if columns are specified, only use those columns, else use all
    - if json result is identical to current file, do not write (thus NOT triggering an ftp sync)
    - add some metadata
    - run rowfunc on each row
    """
    # TODO: try this out for all current lists
    # TODO: update backend handler to accept this common format
    # get table from org file
    table = get_org_table_as_json(fin, table_name)

    # use only selected columns, in specified order
    if columns is not None:
        subtable = [OrderedDict([(k, row[k]) for k in columns]) for row in table]
    else:
        subtable = table

    data = {
        'metadata': {
            'last-updated': dt.strftime(dt.now(), '%Y%m%d'),
        },
        'data': subtable,
    }

    with open(fout, 'r') as f:
        current = json.load(f)
        if current == table:
            print('no change to resulting json, not syncing')
            return

    with open(fout, 'w') as f:
        f.write(json.dumps(data, indent=2))
    print('processed %s -> %s' % (fin, fout))


class ProcessorHandler(FileSystemEventHandler):
    def __init__(self):
        print('ProcessorHandler')

    def on_modified(self, event):
        print(event)
        filename = event.src_path
        if 'todo.txt' in filename:
            # TODO: define these in a list of json objects
            self.process_calls_table(filename)
            # TODO process_org_table(filename, table_name='calls', fout=SYNC + '/webmirror/data/calls.json')
        elif 'buy.txt' in filename:
            self.process_buy_table(filename)
            # TODO process_org_table(filename, table_name='buy', fout=SYNC + '/webmirror/data/buy.json', columns=['item', 'shops', 'tags', 'notes'])
        elif 'read.txt' in filename:
            self.process_books_table(filename)
        elif 'restaurants.txt' in filename:
            self.process_restaurants_table(filename)

    def process_restaurants_table(filename):
        pass

    def process_books_table(filename):
        # TODO add a checkbox for "want to buy" that filters out both "have" and "read"
        pass

    def process_buy_table(self, filename):
        table_name = 'buy'
        columns = ['item', 'shops', 'tags', 'notes']
        fout = SYNC + '/webmirror/data/buy.json'

        # get table from org file
        table = get_org_table_as_json(filename, table_name)

        # use only selected columns, in specified order
        subtable = [OrderedDict([(k, row[k]) for k in columns]) for row in table]

        data = {
            'metadata': {
                'last-updated': dt.strftime(dt.now(), '%Y%m%d'),
            },
            'buy': subtable,
        }

        with open(fout, 'w') as f:
            f.write(json.dumps(data, indent=2))
        print('buy.txt#buy -> data/buy.json')

    def process_calls_table(self, filename):
        table_name = 'calls'
        fout = SYNC + '/webmirror/data/calls.json'

        # get table from org file
        table = get_org_table_as_json(filename, table_name)
        table = {str(n): v for n, v in enumerate(table, 1)}

        # read the file currently in webmirror, only write if changed
        with open(fout, 'r') as f:
            current = json.load(f)
            if current == table:
                print('no change to calls table, not syncing')
                return

        # write to file in webmirror directory
        with open(fout, 'w') as f:
            f.write(json.dumps(table, indent=2))
        print('processed todo.txt#calls -> data/calls.json')


class WebSyncHandler(FileSystemEventHandler):
    def __init__(self, local_path, url, username, password):
        self.local_path = local_path
        self.url = url
        self.username = username
        self.password = password
        print('WebSyncHandler: %s' % local_path)

    # def on_any_event(self, event):
    def on_created(self, event):
        # TODO: implement
        print(event)
        print('handler not implemented')

    def on_modified(self, event):
        # would be nice for syncing to work properly with create, delete, move, etc.
        # but lets just start with the simple stuff
        print(event)
        if not event.__class__.__name__ == 'FileModifiedEvent':
            return
        local_name = event.src_path
        remote_name = local_name.replace(self.local_path, '')
        for ig in ignore_list:
            if ig in local_name:
                return

        # ftp rsync to remote server
        try:
            ftp_session = ftplib.FTP_TLS(self.url, self.username, self.password)
        except Exception as exc:
            print(exc)
            print('error connecting. are you online?')

        self.make_ftp_directories(remote_name)

        with open(local_name, 'rb') as f:
            ftp_session.storlines('STOR ' + remote_name, f)
        print('synced %s -> http://alanbernstein.net%s' % (local_name, remote_name))

        ftp_session.quit()

    def make_ftp_directories(self, remote_name):
        # TODO: implement
        # ftp_session.mkd(pathname) # make dir
        # .cwd(pathname) # set current working directory
        # .pwd get current directory
        pass


def get_web_observer():
    observer = Observer()
    observer.schedule(WebSyncHandler(local_path, server_url, user, password), local_path, recursive=True)
    return observer


def get_processor_observer():
    observer = Observer()
    observer.schedule(ProcessorHandler(), input_path, recursive=True)
    return observer


def main():
    ob1 = get_web_observer()
    ob2 = get_processor_observer()
    ob1.start()
    ob2.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ob1.stop()
        ob2.stop()
    ob1.join()
    ob2.join()

main()
