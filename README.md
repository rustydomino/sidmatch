# sidmatch
sinple Python script to extract and match unique student ID numbers from two CSV files. Fully interactive. Mostly vide coded with ChatGPT 4o. 

Features:
- Uses CSUSB student ID (SID) format of 9 digit number with two leading zeroes (e.g., 001234567). Will also take 7 digit number without leading zeroes.
- SID can be standlone in a column, or be embedded in another string (e,g., a filename extracted to a cell in the csv).
- Prompts user to check if there is a header row, which will be ignored if it exists.
- Supports bash-styled autocomplete when prompting for filenames. 

