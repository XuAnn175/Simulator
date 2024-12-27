#extract the .gz file to .csv file
import os
import gzip

def unzip_file(file_path):
    with gzip.open(file_path, 'rb') as f:
        with open(file_path.replace('.gz', ''), 'wb') as f2:
            f2.write(f.read())

if __name__ == "__main__":
    unzip_file("./BTCUSDT2024-11-27.csv.gz")