from csv import DictReader, DictWriter
from uuid import uuid4
from time import sleep
import re
import os
import logging
import json

import boto3
import xmltodict

import main


SANDBOX_ENDPOINT_URL = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'
PRODUCTION_ENDPOINT_URL = 'https://mturk-requester.us-east-1.amazonaws.com'

DEFAULT_LIFETIME = 60 * 60 * 24
DEFAULT_MAX_ASSIGNMENTS = 1

ID_RE = re.compile(r'^id(\d+)$')
PARAM_RE = re.compile(r'^(?:id\d+|sent\d+)$')

LOGGER = logging.getLogger(__name__)


def loop(model_path, params, hit_type_id, hit_layout_id, num_rounds, client=None, interval=60):
    main.run('generate', model_path, params)
    model_pieces = os.path.basename(os.path.splitext(model_path)[0]).split('_')
    model_dirname = os.path.dirname(model_path)
    model_name = '_'.join(model_pieces[:-1])
    model_start_index = int(model_pieces[-1])

    if client is None:
        client = boto3.client('mturk')

    for round_num in range(num_rounds):
        LOGGER.info('submitting batch')
        batch_data = publish_batch(
            hit_type_id,
            hit_layout_id,
            os.path.join(
                model_dirname,
                '{}_hit_{}{}csv'.format(model_name, model_start_index + round_num + 1, os.extsep)),
            client=client)
        hits = batch_data['hits']
        hit_params = batch_data['hit_params']
        hit_ids = [hit['HITId'] for hit in hits]

        LOGGER.info('waiting on results')
        hit_assignments = wait_hits(hit_ids, client=client, interval=interval)

        LOGGER.info('approving assignments')
        for (hit_id, assignments) in hit_assignments.items():
            approve_assignments([assignment['AssignmentId'] for assignment in assignments],
                                client=client)

        LOGGER.info('writing results')
        write_results(
            os.path.join(
                model_dirname,
                '{}_result_{}{}csv'.format(model_name, model_start_index + round_num + 1, os.extsep)),
            [
                (hit, assignment, hit_params[hit['HITId']])
                for hit in hits
                for assignment in hit_assignments[hit['HITId']]
            ])

        if round_num + 1 < num_rounds:
            operation = 'update-generate'
            LOGGER.info('updating model and generating new HITs')
        else:
            operation = 'update'
            LOGGER.info('updating model')
        main.run(
            operation,
            os.path.join(
                model_dirname,
                '{}_{}{}csv'.format(model_name, model_start_index + round_num, os.extsep)),
            params)


def parse_answer(answer):
    xml_doc = xmltodict.parse(answer)
    return dict(
        (
            answer_field['QuestionIdentifier'],
            answer_field.get('SelectionIdentifier',
                             answer_field.get('FreeText', None))
        )
        for answer_field in xml_doc['QuestionFormAnswers']['Answer'])


def write_results(results_path, hit_assignment_params_triples):
    with open(results_path, 'w', newline='') as f:
        writer = None
        for (hit, assignment, params) in hit_assignment_params_triples:
            row = dict(
                HITId=hit['HITId'],
                HITTypeId=hit['HITTypeId'],
                HITLayoutId=hit['HITLayoutId'],
                AssignmentId=assignment['AssignmentId'],
                WorkerId=assignment['WorkerId'],
            )
            row.update(dict(
                ('Input.{}'.format(k), v)
                for (k, v) in params.items()
            ))
            row.update(dict(
                ('Answer.{}'.format(k), v)
                for (k, v) in parse_answer(assignment['Answer']).items()
            ))
            if writer is None:
                writer = DictWriter(f, fieldnames=sorted(row.keys()))
                writer.writeheader()
            writer.writerow(row)


def approve_assignments(assignment_ids, client=None):
    if client is None:
        client = boto3.client('mturk')
    for assignment_id in assignment_ids:
        LOGGER.info('approving assignment {}'.format(assignment_id))
        client.approve_assignment(AssignmentId=assignment_id)


def publish_batch(hit_type_id, hit_layout_id, batch_csv_path, batch_id=None,
                  lifetime=DEFAULT_LIFETIME, max_assignments=DEFAULT_MAX_ASSIGNMENTS,
                  client=None):
    if batch_id is None:
        batch_id = str(uuid4())
    LOGGER.info('batch id: {}'.format(batch_id))

    if client is None:
        client = boto3.client('mturk')

    hits = []
    hit_params = dict()

    with open(batch_csv_path) as f:
        reader = DictReader(f)
        for (i, row) in enumerate(reader):
            request_token = str(uuid4())
            LOGGER.info('submitting HIT {} (request token {})'.format(i + 1, request_token))
            params = dict((k, v) for (k, v) in row.items() if PARAM_RE.match(k))
            response = client.create_hit_with_hit_type(
                HITTypeId=hit_type_id,
                MaxAssignments=max_assignments,
                LifetimeInSeconds=lifetime,
                UniqueRequestToken=request_token,
                HITLayoutId=hit_layout_id,
                HITLayoutParameters=[
                    dict(Name=k, Value=v) for (k, v) in params.items()
                ],
                RequesterAnnotation=json.dumps(dict(
                    batch_id=batch_id,
                )),
            )
            hit = response['HIT']
            hits.append(hit)
            hit_id = hit['HITId']
            hit_params[hit_id] = params
            LOGGER.info('submitted HIT (id {})'.format(hit_id))

    return dict(batch_id=batch_id, hits=hits, hit_params=hit_params)


def wait_hits(hit_ids, interval=60, client=None):
    if client is None:
        client = boto3.client('mturk')

    hit_assignments = dict()
    for hit_id in hit_ids:
        LOGGER.info('waiting on HIT {}'.format(hit_id))
        hit_assignments[hit_id] = wait_hit(hit_id, interval=interval, client=client)

    return hit_assignments


def wait_hit(hit_id, interval=60, client=None):
    if client is None:
        client = boto3.client('mturk')

    assignments = []

    while not assignments:
        assignment_paginator = client.get_paginator('list_assignments_for_hit')
        assignment_paginate_args = dict(HITId=hit_id)
        assignment_pages = assignment_paginator.paginate(**assignment_paginate_args)
        for assignment_page in assignment_pages:
            for assignment in assignment_page['Assignments']:
                assignments.append(assignment)
        if not assignments:
            sleep(interval)

    return assignments


def hit_in_batch(hit, batch_id):
    try:
        return json.loads(hit['RequesterAnnotation'])['batch_id'] == batch_id
    except KeyError:
        return False
    except json.JSONDecodeError:
        return False


def iter_hit_assignment_pairs(hit_type_id=None, batch_id=None, requester_annotation=None,
                              client=None):
    if client is None:
        client = boto3.client('mturk')
    hit_paginator = client.get_paginator('list_reviewable_hits')
    hit_paginate_args = dict()
    if hit_type_id is not None:
        hit_paginate_args['HITTypeId'] = hit_type_id
    hit_pages = hit_paginator.paginate(**hit_paginate_args)
    for hit_page in hit_pages:
        for hit in hit_page['HITs']:
            if (batch_id is None or hit_in_batch(hit, batch_id)) and (
                    requester_annotation is None or
                    hit['RequesterAnnotation'] == requester_annotation):
                assignment_paginator = client.get_paginator('list_assignments_for_hit')
                assignment_paginate_args = dict(
                    HITId=hit['HITId'],
                    AssignmentStatuses=['Submitted', 'Approved', 'Rejected'])
                assignment_pages = assignment_paginator.paginate(**assignment_paginate_args)
                for assignment_page in assignment_pages:
                    for assignment in assignment_page['Assignments']:
                        yield (hit, assignment)


def list_assignments(hit_type_id=None, batch_id=None, requester_annotation=None,
                     client=None, approve=False):
    if client is None:
        client = boto3.client('mturk')
    hit_id = None
    for (hit, assignment) in iter_hit_assignment_pairs(hit_type_id=hit_type_id, batch_id=batch_id,
                                                       requester_annotation=requester_annotation,
                                                       client=client):
        if hit_id is None or hit['HITId'] != hit_id:
            print(hit['HITId'] + '\t' + hit.get('RequesterAnnotation', ''))
            hit_id = hit['HITId']
        if assignment['AssignmentStatus'] == 'Submitted' and approve:
            client.approve_assignment(AssignmentId=assignment['AssignmentId'])
            assignment = client.get_assignment(AssignmentId=assignment['AssignmentId'])['Assignment']
        print(assignment['WorkerId'] +
              '\t' + assignment['AssignmentId'] +
              '\t' + assignment['AssignmentStatus'] +
              '\n')
