from extract_provisions import extract_ref_sentences
from pathlib import Path

with open('output.txt', 'w') as f:
    for i in range(1,50): #to change accordingly for testing
        filename = "2000_SGCA_" + str(i) + ".txt" #to change accordingly for testing
        my_file = Path(f"./html/{filename}")
        match_num = 1
        if my_file.is_file():
            output = extract_ref_sentences(my_file)
            if len(output) == 0:
                    f.write(f"{filename}: No matches \n\n")
            else:
                f.write(f"{filename}:\n")
                for i in output:
                    f.write(f"{match_num}: {i}\n ----------\n")
                    match_num += 1
                f.write("\n")
