#!/usr/bin/env python3


import boto3

from mturk import print_assignments, PRODUCTION_ENDPOINT_URL, SANDBOX_ENDPOINT_URL


if __name__ == '__main__':
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        description='List all reviewable HITs (optionally for a given HIT '
                    'type id) and their submitted (not yet approved/rejected) '
                    'assignments.',
    )
    parser.add_argument('--hit-type-id',
                        help='Filter results by HIT type id '
                             '(from MTurk web interface)')
    parser.add_argument('--batch-id',
                        help='Filter results by batch id')
    parser.add_argument('--requester-annotation',
                        help='Filter results by exact requester annotation match')
    parser.add_argument('--approve', action='store_true',
                        help='Approve all submitted assignments')
    parser.add_argument('--sandbox', action='store_true',
                        help='Connect to Mechanical Turk sandbox '
                             '(default: production)')
    args = parser.parse_args()
    client = boto3.client(
        'mturk',
        endpoint_url=SANDBOX_ENDPOINT_URL if args.sandbox else PRODUCTION_ENDPOINT_URL)
    print_assignments(hit_type_id=args.hit_type_id, batch_id=args.batch_id,
                      requester_annotation=args.requester_annotation,
                      approve=args.approve, client=client)