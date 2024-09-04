# For Vedic pada_vishleshika: Morphological Analysis
 python3 pada_vishleshika.py WX WX word best -t "vi-balam"
 python3 pada_vishleshika.py WX WX word best -t "rawnaXAwamam"
 python3 pada_vishleshika.py WX roma word best -t "gacCawi"
 python3 pada_vishleshika.py WX roma word best -t "vakrIBavawi"
 python3 pada_vishleshika.py WX deva word best -t "gacMCawi"
 python3 pada_vishleshika.py RN deva sent best -t "vṛṣṭī iva"
 python3 pada_vishleshika.py WX roma word best -t "samavewAH"
 python3 pada_vishleshika.py DN WX word best -t "मामकाः"
 python3 pada_vishleshika.py DN WX word best -t "त्व‍ा॒"
 python3 pada_vishleshika.py DN WX word best -t "इन्द्रगाँ"
 python3 pada_vishleshika.py DN deva word best -t "इन्द्रꣳ"
 python3 pada_vishleshika.py RN WX word best -t "prāṇān"
 python3 pada_vishleshika.py DN deva word best -t "वीडो इति"
 python3 pada_vishleshika.py DN deva word best -t "अकः"
 python3 pada_vishleshika.py DN WX sent best -t "ते त्व‍ा॒ म॒न्थ॒न्तु॒ प्र॒जया॑ स॒ह इ॒ह गृ॒हा॒ण"
 python3 pada_vishleshika.py DN deva word best -t "तन्वम्"
 python3 pada_vishleshika.py DN deva word best -t "हितम्" -o tmp_out_best.tsv
 python3 pada_vishleshika.py DN deva word first -t "हितम्" -o tmp_out_first.tsv
 python3 pada_vishleshika.py DN deva word best -i sample_input_pada_dev.tsv -o sample_padas_out.tsv
 python3 pada_vishleshika.py DN deva word best -t "अजनिष्ठाः"

# For Vedic Word Segmentation and Morphological Analysis
 python3 wsmp_sh_run.py DN deva sent first -i wsmp_sample_input.tsv -o wsmp_sample_output.tsv
 python3 wsmp_sh_run.py DN WX sent first -t "ते त्व‍ा॒ म॒न्थ॒न्तु॒ प्र॒जया॑ स॒ह इ॒ह गृ॒हा॒ण"
