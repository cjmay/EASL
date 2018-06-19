from csv import DictReader
from uuid import uuid4
import re
import os
from time import sleep
import logging

import boto3

import main


SANDBOX_ENDPOINT_URL = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'
PRODUCTION_ENDPOINT_URL = 'https://mturk-requester.us-east-1.amazonaws.com'

DEFAULT_LIFETIME = 60 * 60 * 24
DEFAULT_MAX_ASSIGNMENTS = 1

PARAM_RE = re.compile(r'^(?:id\d+|sent\d+)$')


def loop(model_path, params, num_rounds, endpoint_url=PRODUCTION_ENDPOINT_URL):
    main.run('generate', model_path, params)
    model_pieces = os.path.basename(model_path).split('_')
    model_dirname = os.path.dirname(model_path)
    model_name = '_'.join(model_pieces[:-1])
    model_start_index = int(model_pieces[-1])

    client = boto3.client('mturk', endpoint_url=endpoint_url)

    for round_num in range(num_rounds):
        logging.info('submitting batch')
        batch_data = publish_batch(client=client)
        hit_ids = batch_data['hit_ids']

        logging.info('waiting on results')
        hit_assignment_ids = wait_hits(hit_ids, client=client)

        logging.info('approving assignments')
        for (hit_id, assignment_ids) in hit_assignment_ids.items():
            approve_assignments(assignment_ids, client=client)

        if round_num + 1 < num_rounds:
            operation = 'update-generate'
            logging.info('updating model and generating new HITs')
        else:
            operation = 'update'
            logging.info('updating model')
        main.run(
            operation,
            os.path.join(
                model_dirname,
                '{}_{}{}csv'.format(model_name, model_start_index + round_num, os.extsep)),
            params)


def approve_assignments(assignment_ids, client=None):
    if client is None:
        client = boto3.client('mturk')
    for assignment_id in assignment_ids:
        logging.info('approving assignment {}'.format(assignment_id))
        client.approve_assignment(AssignmentId=assignment_id)


def publish_batch(hit_type_id, hit_layout_id, batch_csv_path, batch_id=None,
                  lifetime=DEFAULT_LIFETIME, max_assignments=DEFAULT_MAX_ASSIGNMENTS,
                  client=None):
    if batch_id is None:
        batch_id = str(uuid4())
    logging.info('batch id: {}'.format(batch_id))

    hit_ids = []
    if client is None:
        client = boto3.client('mturk')
    with open(batch_csv_path) as f:
        reader = DictReader(f)
        for (i, row) in enumerate(reader):
            request_token = str(uuid4())
            logging.info('submitting HIT {} (request token {})'.format(i + 1, request_token))
            response = client.create_hit_with_hit_type(
                HITTypeId=hit_type_id,
                MaxAssignments=max_assignments,
                LifetimeInSeconds=lifetime,
                UniqueRequestToken=request_token,
                HITLayoutId=hit_layout_id,
                HITLayoutParameters=[
                    dict(Name=k, Value=v) for (k, v) in row.items()
                    if PARAM_RE.match(k)
                ],
                RequesterAnnotation='batch:{}'.format(batch_id),
            )
            hit_id = response['HIT']['HITId']
            hit_ids.append(hit_id)
            logging.info('submitted HIT (id {})'.format(hit_id))

    return dict(batch_id=batch_id, hit_ids=hit_ids)


def wait_hits(hit_ids, interval=15, client=None):
    if client is None:
        client = boto3.client('mturk')

    hit_assignment_ids = dict()
    for hit_id in hit_ids:
        logging.info('waiting on HIT {}'.format(hit_id))
        hit_assignment_ids[hit_id] = wait_hit(hit_id, interval=interval, client=client)

    return hit_assignment_ids


def wait_hit(hit_id, interval=15, client=None):
    if client is None:
        client = boto3.client('mturk')

    assignment_ids = set()

    while not assignment_ids:
        assignment_paginator = client.get_paginator('list_assignments_for_hit')
        assignment_paginate_args = dict(HITId=hit_id)
        assignment_pages = assignment_paginator.paginate(**assignment_paginate_args)
        for assignment_page in assignment_pages:
            for assignment in assignment_page['Assignments']:
                assignment_ids.add(assignment['AssignmentId'])
        if not assignment_ids:
            sleep(interval)

    return assignment_ids


def list_assignments(hit_type_id=None, batch_id=None, approve_all=False, client=None):
    if client is None:
        client = boto3.client('mturk')
    hit_paginator = client.get_paginator('list_reviewable_hits')
    hit_paginate_args = dict()
    if hit_type_id is not None:
        hit_paginate_args['HITTypeId'] = hit_type_id
    hit_pages = hit_paginator.paginate(**hit_paginate_args)
    for hit_page in hit_pages:
        for hit in hit_page['HITs']:
            if batch_id is None or hit['RequesterAnnotation'] == 'batch:{}'.format(batch_id):
                print(hit['HITId'] + '\t' + hit.get('RequesterAnnotation', ''))
                assignment_paginator = client.get_paginator('list_assignments_for_hit')
                assignment_paginate_args = dict(HITId=hit['HITId'], AssignmentStatuses=['Submitted'])
                assignment_pages = assignment_paginator.paginate(**assignment_paginate_args)
                for assignment_page in assignment_pages:
                    for assignment in assignment_page['Assignments']:
                        if approve_all:
                            client.approve_assignment(AssignmentId=assignment['AssignmentId'])
                        print('\t' + assignment['AssignmentId'] + ('\tapproved' if approve_all else ''))