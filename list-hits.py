#!/usr/bin/env python3


from mturk import list_assignments


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
    parser.add_argument('--approve-all', action='store_true',
                        help='Approve all submitted assignments')
    args = parser.parse_args()
    list_assignments(hit_type_id=args.hit_type_id, batch_id=args.batch_id,
                     approve_all=args.approve_all)