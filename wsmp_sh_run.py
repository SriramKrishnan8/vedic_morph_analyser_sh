#!/usr/bin/env python3

import os
import sys
import subprocess as sp

import argparse
import multiprocessing as mp

import re
import json
from tqdm import tqdm

import devtrans as dt

from wsmp_sh import *

def main():
    """ """
    
    # Parsing Arguments
    parser = argparse.ArgumentParser()
    
    # Mandatory Arguments
    parser.add_argument(
        "input_enc", default="WX",
        choices=["DN", "KH", "RN", "SL", "VH", "WX"],
        help="input encoding"
    )
    parser.add_argument(
        "output_enc", default="roma",
        choices=["deva", "roma", "WX"],
        help="output encoding"
    )
    parser.add_argument(
        "text_type", default="sent",
        choices=["word", "sent"],
        help="input text type"
    )
    parser.add_argument(
        "seg_mode", default="first",
        choices=["first", "best"],
        help="first - first solution; or best - best (10) solutions"
    )
    
    # Options (one of -t or -i, -o is mandatory)
    parser.add_argument(
        "-t", "--input_text", type=str,
        help="input string"
    )
    parser.add_argument(
        "-i", "--input_file", type=argparse.FileType('r', encoding='UTF-8'),
        help="reads from file if specified"
    )
    parser.add_argument(
        "-o", "--output_file", type=argparse.FileType('w', encoding='UTF-8'),
        help="for writing to file"
    )
    
    args = parser.parse_args()
    
    if args.input_file and args.input_text:
        print("Please specify either input text ('-t') or input file ('-i, -o')")
        sys.exit()
    
    input_enc = args.input_enc
    output_enc = args.output_enc
    seg_mode = segmentation_modes.get(args.seg_mode, "f")
    txt_type = text_types.get(args.text_type, "t")
    
    if args.input_file:
        i_file = args.input_file.name
        o_file = args.output_file.name if args.output_file else "output.txt"
        run_sh_file(
            i_file, o_file, input_enc, lex="MW",
            us="f", output_encoding=output_enc,
            segmentation_mode=seg_mode, text_type=txt_type, stemmer="t"
        )
    elif args.input_text:
        res = run_sh_text(
            args.input_text, input_enc, lex="MW",
            us="f", output_encoding=output_enc,
            segmentation_mode=seg_mode, text_type=txt_type, stemmer="t"
        )
        if args.output_file:
            with open(args.output_file.name, 'w', encoding='utf-8') as o_file:
                json.dump(res, o_file, ensure_ascii=False)
        else:
            print(json.dumps(res, ensure_ascii=False))
    else:
        print("Please specify one of text ('-t') or file ('-i & -o')")
        sys.exit()
    

if __name__ == "__main__":
    main()
