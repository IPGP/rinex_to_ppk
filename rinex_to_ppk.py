#!/usr/bin/env python3
# pylint: disable=no-member

import csv
from argparse import ArgumentParser,  RawDescriptionHelpFormatter
from dataclasses import dataclass
from math import cos, radians
from os.path import basename,dirname

import numpy as np

DEGREE_LAT_IN_METERS = 10000000/90

@dataclass
class PpkTimestamp:
    """Calculate position from ppk timestamp"""

    a_column: str
    b_column: float
    d_column: str
    e_column: str
    f_column: str
    ph4_base_file: str

    def calculate_values(self, pos_data_float, file_index):
        northing_diff = float(self.d_column.strip().split(',', maxsplit=1)[0])
        easting_diff = float(self.e_column.strip().split(',', maxsplit=1)[0])
        elevation_diff = float(self.f_column.strip().split(',', maxsplit=1)[0])

        # Find nearest Timestamp
        for idx, line in enumerate(pos_data_float):
            if line[1] > self.b_column:
                inf = pos_data_float[idx-1]
                sup = pos_data_float[idx]
                break
        percent_diff_between_timestamps = (self.b_column - inf[1])/(sup[1]-inf[1])
        interpolated_lat = (
            inf[2]*(1-percent_diff_between_timestamps)+sup[2]*percent_diff_between_timestamps)
        interpolated_lon = (
            inf[3]*(1-percent_diff_between_timestamps)+sup[3]*percent_diff_between_timestamps)
        interpolated_alti = (
            inf[4]*(1-percent_diff_between_timestamps)+sup[4]*percent_diff_between_timestamps)

        degree_lon_in_meters = DEGREE_LAT_IN_METERS*cos(radians(inf[2]))

        lat_diff_deg = northing_diff / 1000 / DEGREE_LAT_IN_METERS
        lon_diff_deg = easting_diff / 1000 / degree_lon_in_meters
        alti_diff = elevation_diff / 1000

        new_lat = interpolated_lat + lat_diff_deg
        new_lon = interpolated_lon + lon_diff_deg
        new_alt = interpolated_alti - alti_diff

        print(f'{self.ph4_base_file}_{file_index:0>4}.JPG\t{new_lon}\t{new_lat}\t{new_alt}')
        return f'{self.ph4_base_file}_{file_index:0>4}.JPG\t{new_lon}\t{new_lat}\t{new_alt}\n'

#        print(f'{self.ph4_base_file}_{file_index:0>4}.JPG\t{new_lat}\t{new_lon}\t{new_alt}')
#        return f'{self.ph4_base_file}_{file_index:0>4}.JPG\t{new_lat}\t{new_lon}\t{new_alt}\n'


@dataclass
class RinexToPpk:
    """Import calculated RINEX from PH4RTK with images date and find accurate PPK positions"""
    data_dir: str
    timestamp_file: str = ''
    pos_ph4_rinex_file: str =''
    zone_name: str =''

    def __post_init__(self):
            #ex avec  self.data_dir = [/data/images/2022_11_21_mayotte/25_11_2022/100_0004/]
            #print(f'self.data_dir {self.data_dir}')
            self.data_dir=self.data_dir[0]
            # self.data_dir=/data/images/2022_11_21_mayotte/25_11_2022/100_0004/
            #print(f'self.data_dir {self.data_dir}')
            self.data_dir='/'+self.data_dir.strip("/")
            # self.data_dir=/data/images/2022_11_21_mayotte/25_11_2022/100_0004            
            #print(f'self.data_dir {self.data_dir}')
            self.zone_name=basename(self.data_dir)
            #print(f'self.zone_name {self.zone_name}')
            # self.zone_name=100_0004

            # si le nom du repertoire contient plusiers '_' on garde les 8 premier caracteres
            if self.zone_name.count('_'):
                self.zone_name=self.zone_name[0:8]


            self.timestamp_file=self.data_dir+'/'+self.zone_name+'_Timestamp.MRK'
            #print(f'self.timestamp_file {self.timestamp_file}')

            self.pos_ph4_rinex_file=self.data_dir+'/'+self.zone_name+'_Rinex.pos'
            #print(f'self.pos_ph4_rinex_file {self.pos_ph4_rinex_file}')


    def calculate_ppk_positions(self):
        """Calculate position from ppk data"""
        #        __import__("IPython").embed()
        #        sys.exit()
        #print(f'open self.pos_ph4_rinex_file {self.pos_ph4_rinex_file}')
        with open(self.pos_ph4_rinex_file,'r') as rinex_file:

            # skip headers
            rinex_file.readline()
            rinex_file.readline()

            pos_data = list(csv.reader(rinex_file, delimiter=','))
            pos_data_float = np.asfarray(pos_data, dtype=float)

        #ph4_part_a,ph4_part_b,_ = basename(self.timestamp_file.name).split('_')

        #ph4_base_file=f'{data_dir}{ph4_part_a}_{ph4_part_b}'
        final_file=f'{self.data_dir}/geo.txt'
        file_index = 1
        with open(final_file,'w',encoding="UTF_8") as output_csv:
        #with open(f'{ph4_base_file}_PPK.csv','w',encoding="UTF_8") as output_csv:
            output_csv.write("EPSG:4326\n")
            with open(self.timestamp_file,'r') as timestamp_file:
                for line in timestamp_file:
                    a_column, b_column, _, d_column, e_column, f_column, _, _, _, _, _ = line.split('\t')
                    result = PpkTimestamp(a_column, float(b_column), d_column, e_column, f_column, self.zone_name).calculate_values(pos_data_float, file_index)
                    output_csv.write(result)
                    file_index = file_index+1
        print(f'{final_file} successfully created')


def parse_arguments():
    parser = ArgumentParser(prog='RinexRoPPK',
        formatter_class=RawDescriptionHelpFormatter,
        description='''Create geo.txt with Rinex File form RTKPOST and Timestamp.MRK
        in image directory 
        ''')

    parser.add_argument(
        'input_dir', 
        metavar='PATH',nargs=1,
        help="Directory of the data from RTKPOST.")

    return parser


def main():
    arguments=parse_arguments()
    args=arguments.parse_args()

    rinextoppk = RinexToPpk(args.input_dir)
    rinextoppk.calculate_ppk_positions()


if __name__ == "__main__":
    main()
