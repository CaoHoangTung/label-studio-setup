import argparse
from openmovement.load import CwaData

#Convert cwa format into ndarray
def process_file(args):
    with CwaData(args.input, include_gyro=False, include_temperature=True) as cwa_data: #Convert cwa format into ndarray
        # As a pandas DataFrame
        samples = cwa_data.get_samples()
        samples.to_csv(args.output, index=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process input file and write the result to an output file.')
    parser.add_argument('--input', default='./upwatch_data/26892_0000050052.cwa', help='Path to the input file')
    parser.add_argument('--output', default='./upwatch_data/26892_0000050052.csv', help='Path to the output file')

    args = parser.parse_args()

    process_file(args)
