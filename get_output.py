from extract_provisions import extract_ref_sentences
from pathlib import Path


# with open('output.txt', 'w') as f: #change output fil name based on the year you want to test
#     for i in range(1,10): #to change accordingly for testing
#         filename = "2021_SGHC_" + str(i) + ".txt" #to change accordingly for testing
#         my_file = Path(f"./html/{filename}")
#         match_num = 1
#         if my_file.is_file():
#             output = extract_ref_sentences(my_file)
#             if len(output) == 0:
#                     f.write(f"{filename}: No matches \n\n")
#             else:
#                 f.write(f"{filename}:\n")
#                 for i in output:
#                     f.write(f"{match_num}: {i}\n ----------\n")
#                     match_num += 1
#                 f.write("\n")

#this is the function for above
def write_output_to_file(year =2021, type="SGCA", start_number= 1, end_number=100, output_file = 'output_2021'):
    with open(f"{output_file}.txt", 'w') as f: 
        for i in range(start_number,end_number+1): 
            filename = str(year) + "_" + type + "_" + str(i) + ".txt" 
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

write_output_to_file(2021, "SGCA", 1, 10, "output_2021")