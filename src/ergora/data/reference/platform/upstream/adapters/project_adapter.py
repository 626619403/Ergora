#!/usr/bin/env python3
"""Project-owned adapter. Fails closed until setup PR implements real entry points."""
import argparse, sys
p=argparse.ArgumentParser()
p.add_argument('action',choices=['doctor','capture','verify','measure','collect'])
p.add_argument('--manifest');p.add_argument('--arm',choices=['baseline','candidate'])
p.add_argument('--pair-id');p.add_argument('--output')
a=p.parse_args()
print('NOT_CONFIGURED: implement '+a.action+' against the actual training entry and scheduler.',file=sys.stderr)
sys.exit(2)
