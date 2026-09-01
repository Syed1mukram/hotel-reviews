HOTEL SCRIPT GENERATOR V3

V3 fixes the short-script problem by generating the narration in 8 sections while
loading the model only once. Target is about 1,300-1,500 words.

Kaggle:
python /path/script_generator.py --input /path/hotel_data_sample.json --output /kaggle/working/hotel_script.txt

The script uses only facts present in the JSON and omits prohibited content.
