"""UTF-8 JSON CLI. Output replacement occurs only after successful validation."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from .core import solve
from .verify import verify
from .subsets import analyze


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description='Finite first-order unification and rewrite-certificate verification')
    modes=p.add_mutually_exclusive_group()
    modes.add_argument('--subsets',action='store_true',help='enumerate indexed equation subsets, minimal conflicts and deletion repairs')
    modes.add_argument('--verify',action='store_true',help='check a supplied rewrite certificate without calling solve')
    p.add_argument('input',help='JSON path or - for stdin')
    p.add_argument('-o','--output',help='output JSON path; default stdout')
    args=p.parse_args(argv)
    try:
        byte_limit=67108864 if args.verify else 65536
        if args.input=='-': raw=sys.stdin.buffer.read(byte_limit+1)
        else:
            with open(args.input,'rb') as stream:raw=stream.read(byte_limit+1)
        if len(raw)>byte_limit:
            raise ValueError('input exceeds '+str(byte_limit)+' UTF-8 bytes')
        data=json.loads(raw.decode('utf-8'),object_pairs_hook=unique_object,
                        parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON constant')))
        result={'valid':verify(data)} if args.verify else analyze(data) if args.subsets else solve(data)
        text=json.dumps(result,ensure_ascii=True,allow_nan=False,indent=2)+'\n'
        if args.output:
            target=Path(args.output)
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=target.parent,delete=False) as f:
                tmp=f.name
                try:f.write(text)
                except BaseException:
                    os.unlink(tmp)
                    raise
            try:os.replace(tmp,target)
            except BaseException:
                os.unlink(tmp)
                raise
        else:sys.stdout.write(text)
    except (ValueError,OSError,UnicodeError,RecursionError) as e:
        p.exit(2,'Invalid input: '+str(e)+'\n')
    return 0

if __name__=='__main__':raise SystemExit(main())
