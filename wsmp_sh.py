#!/usr/bin/env python3

import os
import sys
import subprocess as sp

import argparse
import multiprocessing as mp

import psutil

import re
import json
from tqdm import tqdm

import devtrans as dt

# Import roots when deeper roots are required
# import roots as rt


segmentation_modes = {
    "first" : "s",
    "best" : "l"
}

text_types = {
    "word" : "f",
    "sent" : "t"
}

cgi_file = os.path.join(os.path.dirname(__file__), "interface2")
# If Sanskrit Heritage Platform is already installed, 
# uncomment the following and replace with your cgi bin path
# cgi_file = "/usr/lib/cgi-bin/SKT/sktgraph2"

time_out = 30


def remove_svaras(text):
    """ Removes svaras
    """

    new_text = []
    for char in text:
        if '\u0951' <= char <= '\u0954':
            continue
        # To remove zero width joiner character
        elif char == '\u200d':
            continue
        new_text.append(char)
    
    modified_text = "".join(new_text)
    
    return modified_text


def handle_input(input_text, input_encoding):
    """ Modifies input based on the requirement of the Heritage Engine
    """
    
    # Remove svaras in the input text as these are not analysed 
    # properly by the Sanskrit Heritage Segmenter
    modified_input = remove_svaras(input_text)

    # Replace special characters with " " since Heritage Segmenter
    # does not accept special characters except "|", "!", "."
    modified_input = re.sub(r'[$@#%&*()\[\]=+:;"}{?/,\\-]', ' ', modified_input)
    if not (input_encoding == "RN"):
        modified_input = modified_input.replace("'", " ")
    
    # The following condition is added to replace chandrabindu
    # which comes adjacent to characters, with m or .m 
    # depending upon its position
    if input_encoding == "DN":
        chandrabindu = "ꣳ"
        if chandrabindu in modified_input:
            if modified_input[-1] == chandrabindu:
                modified_input = modified_input.replace("ꣳ", "म्")
            else:
                modified_input = modified_input.replace("ꣳ", "ं")
        else:
            pass
    else:
        pass
    
    normalized_input = re.sub(r'M$', 'm', modified_input)
    normalized_input = re.sub(r'\.m$', '.m', normalized_input)
    
    return normalized_input


def input_transliteration(input_text, input_enc):
    """ Converts input in any given notation to WX  
    """
    
    trans_input = ""
    trans_enc = ""
    
    if input_enc == "DN":
        trans_input = dt.slp2wx(dt.dev2slp(input_text))
        trans_input = trans_input.replace("ळ्", "d")
        trans_input = trans_input.replace("ळ", "d")
        trans_input = trans_input.replace("kdp", "kLp")
        trans_enc = "WX"
    elif input_enc == "RN":
        trans_input = dt.slp2wx(dt.iast2slp(input_text))
        trans_enc = "WX"
    else:
        trans_input = input_text
        trans_enc = input_enc
    
    # The following condition makes sure that the chandrabindu
    # which comes on top of other characters is replaced with m
    if "z" in trans_input:
        if trans_input[-1] == "z":
            trans_input = trans_input.replace("z", "m")
        else:
            trans_input = trans_input.replace("z", "M")
    
    return (trans_input, trans_enc)


def output_transliteration(output_text, output_enc):
    """ Converts the output which is always in WX to 
        deva or roma
    """
    
    trans_output = ""
    trans_enc = ""
    
    if output_enc == "deva":
        trans_output = dt.slp2dev(dt.wx2slp(output_text))
        # NOTE: WX 2 SLP conversion of double avagraha results into ''.
        # Fix it
        num_map = str.maketrans('०१२३४५६७८९', '0123456789')
        trans_output = trans_output.translate(num_map)
        trans_enc = "deva"
    elif output_enc == "roma":
        trans_output = dt.slp2iast(dt.wx2slp(output_text))
        trans_enc = "roma"
    else:
        trans_output = output_text
        trans_enc = output_enc
    
    return (trans_output, trans_enc)


def run_sh(input_text, input_encoding, lex="MW", us="f",
           output_encoding="roma", segmentation_mode="b", text_type="t", stemmer="t"):
    """ Runs the cgi file with a given word.  
        
        Returns a JSON
    """
    
    out_enc = output_encoding if output_encoding in ["roma", "deva"] else "roma"
    
    env_vars = [
        "lex=" + lex,
        "us=" + us,
        "st=" + text_type,
        "font=" + out_enc,
        "t=" + input_encoding,
        "text=" + input_text,#.replace(" ", "+"),
        "mode=" + segmentation_mode,
        "stemmer=" + stemmer
    ]
    
    # Set the directory for the subprocess to the directory of cgi_file
    working_dir = os.path.dirname(cgi_file)
    
    query_string = "QUERY_STRING=\"" + "&".join(env_vars) + "\""
    command = query_string + " " + cgi_file
    
    try:
        p = sp.Popen(
            command,
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            shell=True,
            cwd=working_dir  # Set working directory to access vedic/data
        )
        
        outs, errs = p.communicate(timeout=time_out)
    except sp.TimeoutExpired:
        parent = psutil.Process(p.pid)
        for child in parent.children(recursive=True):
            child.terminate()
            parent.terminate()
        result = ""
        status = "Timeout"
    except Exception as e:
        result = ""
        status = "Failure"
    else:
        result = outs.decode('utf-8')
        status = "Success"
    
    return result, status


def identify_stem_root(d_stem, base, d_morph, i_morphs):
    """ The output JSON object keys derived_stem and base are modified
        to stem and root based on the inflectional and derivational
        morphological analyses
    """

    root = ""
    stem = ""

    verb_identifiers = [
        "pr.", "imp.", "opt.", "impft.", "inj.", "subj.", "pft.", "plp.",
        "fut.", "cond.", "aor.", "ben.", "abs.", "inf."
    ]

    noun_identifiers = [
        "nom.", "acc.", "i.", "dat.", "abl.", "g.", "loc.", "voc.", "iic.",
        "iiv.", "part.", "prep.", "conj.", "adv.", "tasil", "ind."
    ]

    if d_morph:
        root = base
        stem = d_stem
    else:
        morph_keys = " ".join(i_morphs).split(" ")
        for m in morph_keys:
            if m in verb_identifiers:
                root = d_stem
                break
            if m in noun_identifiers:
                stem = d_stem
                
                # The following conditions are present for stems which
                # are derived from roots but SH does not produce a 
                # derivational morphological analysis
                # if d_stem in rt.sh_roots:
                #     root = d_stem
                # elif d_stem.split("#")[0] in rt.scl_roots:
                #     root = d_stem.split("#")[0]
                # else:
                #     stem = d_stem
                break
    
    return (root, stem)


def get_morphological_analyses(input_out_enc, result_json, out_enc):
    """ Returns the results from the JSON
    """
    
    analysis_json = {}

    seg = result_json.get("segmentation", [])
    morphs = result_json.get("morph", [])

    if morphs:
        new_morphs = []

        for m in morphs:
            word = m.get("word", "")
            d_stem = m.get("derived_stem", "")
            base = m.get("base", "")
            d_morph = m.get("derivational_morph", "")
            i_morphs = m.get("inflectional_morphs", [])

            root, stem = identify_stem_root(d_stem, base, d_morph, i_morphs)
            
            new_item = {}
            new_item["word"] = output_transliteration(word, out_enc)[0]
            new_item["stem"] = output_transliteration(stem, out_enc)[0]
            new_item["root"] = output_transliteration(root, out_enc)[0]
            new_item["derivational_morph"] = d_morph
            new_item["inflectional_morphs"] = i_morphs

            new_morphs.append(new_item)
        
        words = [output_transliteration(wrd, out_enc)[0] for wrd in seg]
        analysis_json["input"] = input_out_enc
        analysis_json["status"] = "success"
        analysis_json["segmentation"] = words
        analysis_json["morph"] = new_morphs
        analysis_json["source"] = "SH"

    return analysis_json
    

def extract_result(result):
    """ Extracts Result as JSON
    """ 
    
    result_json = {}
    
    if result:
        try:
            result_str = result.split("\n")[-1]
            result_json = json.loads(result_str)
        except Exception as e:
            result_json = {}
    
    return result_json


def handle_result(result, input_word, output_enc, issue, text_type):
    """ Returns the results from the JSON
    """
    
    status = "Failure"

    # print(result)

    result_json = extract_result(result)
    
    seg = result_json.get("segmentation", [])
    morphs = result_json.get("morph", [])

    if seg:
        if "error" in seg[0]:
            status = "Error"
            message = seg[0]
        elif ("#" in seg[0] or "?" in seg[0]) and (text_type == "w" or " " not in seg[0]):
            status = "Unrecognized"
            message = "SH could not recognize at least on chunk / word"
        else:
            status = "Success"
    else:
        if issue == "Timeout":
            status = "Timeout"
            message = "SH could not produce the response within " + str(time_out) + "s"
        elif issue == "input":
            status = "Error"
#            seg = ["Error in Input / Output Convention. Please check the input"]
            message = "Error in Input / Output Convention. Please check the input"
        else:
            status = "Unknown Anomaly"
            message = "An unknown error occurred"

    morph_analysis = {}
    
    if status == "Timeout":
        morph_analysis["input"] = input_word
        morph_analysis["status"] = "timeout"
        morph_analysis["error"] = message
    elif status == "Unknown Anomaly":
        morph_analysis["input"] = input_word
        morph_analysis["status"] = issue
        morph_analysis["error"] = message
    elif status == "Failure":
        morph_analysis["input"] = input_word
        morph_analysis["status"] = "failed"
        morph_analysis["error"] = message
    elif status == "Error":
        morph_analysis["input"] = input_word
        morph_analysis["status"] = "error"
        morph_analysis["error"] = message
    elif status == "Unrecognized":
        morph_analysis["input"] = input_word
        morph_analysis["status"] = "unrecognized"
        morph_analysis["error"] = message
    else: # Success
        morph_analysis = get_morphological_analyses(input_word, result_json, output_enc)
    
    return morph_analysis


def merge_sent_analyses(sub_sent_analysis_lst, output_encoding):
    """ """
    
    input_sent = []
    status = []
    segmentation = []
    morph = []
    err = []
    
    i = 1
    for sub_sent_analysis in sub_sent_analysis_lst:
        cur_input = sub_sent_analysis.get("input", "")
        cur_status = sub_sent_analysis.get("status", "")
        cur_segmentation = sub_sent_analysis.get("segmentation", [])
        cur_morph = sub_sent_analysis.get("morph", [])
        cur_err = sub_sent_analysis.get("error", "")
        
        input_sent.append(cur_input)
        status.append(cur_status)
        segmentation += cur_segmentation
        morph += cur_morph
        
        if cur_err:
            c = "Error in " + str(i) + ": " + cur_err
        else:
            c = str(i) + ":-"
        err.append(c)

        i += 1
    
    full_stop_dict = {
        "deva": " । ", "wx" : " . ", "roma": " . ",
    }
    
    full_stop = full_stop_dict.get(output_encoding, " . ")
    
    merged_analysis = {}
    merged_analysis["input"] = full_stop.join(input_sent)
    
#    status_val = "success" if "success" in status else "failure"
    status_val = "success" if "success" in status else status[0]
    merged_analysis["status"] = status_val
    
    merged_analysis["segmentation"] = [] if not segmentation else [ full_stop.join(segmentation) ]
    merged_analysis["morph"] = morph
    merged_analysis["error"] = ";".join(err)
    merged_analysis["source"] = "SH"
    
    return merged_analysis


def run_sh_text(input_sent, input_encoding, lex="MW",
                us="f", output_encoding="roma",
                segmentation_mode="b", text_type="t", stemmer="t"):
    """ Handles morphological analyses for the given input word
    """
    
    # SH does not accept special characters in the input sequence.  
    # And it results errors if such characters are found.  
    # Uncomment the following to find the morphological analyses of the
    # word by ignoring the special characters.  
    
    issue = ""
    input_sent_out_enc = input_sent

    i_word = handle_input(input_sent.strip(), input_encoding)
    trans_input, trans_enc = input_transliteration(i_word, input_encoding)
    
    sub_sent_list = list(filter(None, trans_input.split(".")))
    sub_sent_analysis_lst = []
    for sub_sent in sub_sent_list:
        try:
            result, issue = run_sh(
                sub_sent.strip(), trans_enc, lex, us, output_encoding, 
                segmentation_mode, text_type, stemmer
            )
        except Exception as e:
            result = ""
            issue = e
        
        input_sent_out_enc = output_transliteration(sub_sent.strip(), output_encoding)[0]
        
        sub_sent_analysis = handle_result(
            result, input_sent_out_enc, output_encoding, issue, text_type
        )
        sub_sent_analysis_lst.append(sub_sent_analysis)
    
    sent_analysis = merge_sent_analyses(sub_sent_analysis_lst, output_encoding)
    
    return sent_analysis


def process_words_subset(input_list, input_encoding, lex, us,
                        output_encoding, segmentation_mode, stemmer, text_type,
                        start, end, result_queue):
    """ """
    
    results = []
    for input_word in input_list[start:end]:
        res = run_sh_text(
            input_word, input_encoding, lex, us, output_encoding,
            segmentation_mode, text_type, stemmer
        )
        results.append(res)
    
    result_queue.put(results)


def run_sh_parallely(input_list, input_encoding, lex, us,
                     output_encoding, segmentation_mode, text_type, stemmer):
    """ """
    
    num_processes = mp.cpu_count()
    chunk_size = len(input_list) // num_processes
    
    chunks = [input_list[i:i + chunk_size] for i in range(0, len(input_list), chunk_size)]
    
    result_queue = mp.Queue()
    
    processes = []
    for chunk in chunks:
        cur_args = (
            chunk, input_encoding, lex, us, output_encoding,
            segmentation_mode, text_type, stemmer, 0, len(chunk), result_queue
        )
        process = mp.Process(target=process_words_subset, args=cur_args)
        processes.append(process)
        process.start()
        
    for process in processes:
        process.join()
    
    results = []
    while not result_queue.empty():
        results.extend(result_queue.get())
        
    return results
    

def run_sh_sequentially(input_list, input_encoding, lex, us,
                        output_encoding, segmentation_mode, text_type, stemmer):
    """ """
    
    output_list = []
    for i in tqdm(range(len(input_list))):
        input_sent = input_list[i].strip()
        
        sent_analysis = run_sh_text(
            input_sent, input_encoding, lex, us, output_encoding,
            segmentation_mode, text_type, stemmer
        )
        
        output_list.append(sent_analysis)
    
    return output_list


def run_sh_file(input_file, output_file, input_encoding, lex="MW",
                us="f", output_encoding="roma", segmentation_mode="b",
                text_type="t", stemmer="t"):
    """ Handles morphological analyses for all the sentences in a file
    """

    try:
        ifile = open(input_file, 'r', encoding='utf-8')
    except OSError as e:
        print(f"Unable to open {path}: {e}", file=sys.stderr)
        sys.exit(1)
        
    input_text = ifile.read()
    ifile.close()

    if input_text.strip() == "":
        print("Specified input file does not have any sentence.")
        sys.exit(1)
    
    i_list = [sent for sent in input_text.strip().split("\n")]
    input_list = list(filter(None, i_list))

    # Temporarily parallel processing is disabled
    parallel = False
    
    if parallel:
        output_list = run_sh_parallely(
            input_list, input_encoding, lex, us, output_encoding,
            segmentation_mode, text_type, stemmer
        )
    else:
        output_list = run_sh_sequentially(
            input_list, input_encoding, lex, us, output_encoding,
            segmentation_mode, text_type, stemmer
        )
    
    with open(output_file, 'w', encoding='utf-8') as out_file:
#        if the output is required to be in JSON format
#        json.dump(output_list, out_file, ensure_ascii=False)
#        if the output is required to be in a list format
        output_contents = [ json.dumps(item, ensure_ascii=False) for item in output_list ]
        out_file.write("\n".join(output_contents))


