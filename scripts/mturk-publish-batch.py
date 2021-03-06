#!/usr/bin/env python3


import boto3

from easl.mturk import (
    publish_batch, DEFAULT_LIFETIME, DEFAULT_MAX_ASSIGNMENTS,
    PRODUCTION_ENDPOINT_URL, SANDBOX_ENDPOINT_URL,
)


if __name__ == '__main__':
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        description='Read a csv file of Mechanical Turk batch (HIT) data and '
                    'submit a HIT for each line, mimicking the web interface.',
    )
    parser.add_argument('hit_type_id',
                        help='HIT type id (from MTurk web interface)')
    parser.add_argument('hit_layout_id',
                        help='HIT layout id (from MTurk web interface)')
    parser.add_argument('batch_csv_path',
                        help='Path to Mechanical Turk batch csv data')
    parser.add_argument('--batch-id',
                        help='Identifier for this batch of HITs '
                             '(if not specified, generate uuid)')
    parser.add_argument('--lifetime', type=int, default=DEFAULT_LIFETIME,
                        help='Lifetype of HIT (in seconds)')
    parser.add_argument('--max-assignments', type=int, default=DEFAULT_MAX_ASSIGNMENTS,
                        help='Max number of assignments per HIT')
    parser.add_argument('--sandbox', action='store_true',
                        help='Connect to Mechanical Turk sandbox '
                             '(default: production)')
    args = parser.parse_args()
    client = boto3.client(
        'mturk',
        endpoint_url=SANDBOX_ENDPOINT_URL if args.sandbox else PRODUCTION_ENDPOINT_URL)
    publish_batch(args.hit_type_id, args.hit_layout_id, args.batch_csv_path,
                  batch_id=args.batch_id,
                  lifetime=args.lifetime, max_assignments=args.max_assignments,
                  client=client)
