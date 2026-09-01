HOTEL SCRIPT GENERATOR V4

V4 keeps the 8-section approach but tightens section targets and adds a final
sentence-boundary safety cap. Target is approximately 1,350-1,450 words,
roughly 9-10 minutes at 150 words per minute.

Kaggle command:
python /path/script_generator.py --input /path/hotel_data_sample.json --output /kaggle/working/hotel_script.txt

Uses only supplied hotel facts and omits prohibited content.
