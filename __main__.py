import time
import shutil
import os
from wall import create_3d_prisms_from_shapefile
from separate_obj import split_obj_by_shapefile
from tocityjson import obj_to_cityjson

#UBAH BAGIAN INI
input_bo = './input/bo_Bontang.shp'
input_ohm = './input/OHM AOI Kampung Timur Balaikota Bontang.tif'
epsg = 32650
output_ctyjson = './output/Bontang_LOD1.json'

#JANGAN DIUBAH
temp = './temp'
output_obj1 = os.path.join(temp,'./objlod1.obj')
output_sep1 = os.path.join(temp,'./sep_folder')

def create_temp(temp):
    if not os.path.exists(temp):
        os.makedirs(temp)
def clear(temp):
    if os.path.exists(temp):
        shutil.rmtree(temp)
def main():
    create_temp(temp)
    try:
        start = time.time()
        create_3d_prisms_from_shapefile(input_bo,input_ohm,output_obj1)
        print(f"Pembuatan LOD 1 selesai dalam {time.time() - start:.2f} detik")

        start = time.time()
        split_obj_by_shapefile(output_obj1, input_bo, output_sep1, 0.001)
        print(f"Pemisahan OBJ selesai dalam {time.time() - start:.2f} detik")

        start = time.time()
        obj_to_cityjson(output_sep1, output_ctyjson, epsg)
        print(f"Objek berhasil dikonversi ke dalam format CityJSON dalam {time.time() - start:.2f} detik")
    
    finally:
        clear(temp)

if __name__ == "__main__":
    main()
