import geopandas as gpd
import rasterio
from rasterstats import zonal_stats
from shapely.geometry import Polygon, Point
import trimesh
import numpy as np
from scipy.spatial import Delaunay
from tqdm import tqdm  

def create_3d_prisms_from_shapefile(shapefile_path, raster_path, output_path):
    """
    Membuat model 3D prisma dari shapefile dan TIF raster dengan ketinggian sesuai rata-rata nilai raster.

    Parameters:
        shapefile_path (str): Path ke file shapefile input.
        raster_path (str): Path ke file TIF raster input.
        output_path (str): Path untuk menyimpan file OBJ output.

    Returns:
        None
    """
    # Langkah 1: Memuat shapefile
    gdf = gpd.read_file(shapefile_path)

    # Langkah 2: Menghitung zonal statistik rata-rata nilai OHM TIF di setiap poligon
    with rasterio.open(raster_path) as src:
        affine = src.transform
        array = src.read(1)
        stats = zonal_stats(gdf, array, affine=affine, stats=['mean'])

    # Menambahkan kolom elevasi rata-rata ke geodataframe
    gdf['elevation'] = [stat['mean'] for stat in stats]

    # Langkah 3: Membuat prisma 3D dari poligon dengan ketinggian sesuai elevasi rata-rata
    meshes = []
    print("Membuat model 3D prisma:")
    for idx, row in tqdm(gdf.iterrows(), total=len(gdf), desc="Processing Polygons"):
        polygon = row['geometry']
        elevation = row['elevation']

        if isinstance(polygon, Polygon):
            # Mendapatkan koordinat dari poligon
            base_coords = np.array(polygon.exterior.coords)
            
            # Membuat dua set titik: dasar (Z=0) dan atas (Z=elevation)
            base_vertices = np.column_stack((base_coords[:, 0], base_coords[:, 1], np.zeros(base_coords.shape[0])))
            top_vertices = np.column_stack((base_coords[:, 0], base_coords[:, 1], np.full(base_coords.shape[0], elevation)))
            
            # Menggabungkan dasar dan atas ke dalam satu array
            vertices = np.vstack((base_vertices, top_vertices))
            
            # Menggunakan Delaunay triangulation untuk membuat tutup dasar
            delaunay = Delaunay(base_coords[:, :2])
            base_faces = []
            top_faces = []

            # Memfilter segitiga yang berada di luar poligon
            for simplex in delaunay.simplices:
                # Mendapatkan centroid segitiga
                tri_points = base_coords[simplex]
                centroid = np.mean(tri_points, axis=0)
                
                # Jika centroid segitiga berada di dalam poligon, tambahkan segitiga ini
                if polygon.contains(Point(centroid)):
                    base_faces.append(simplex)
                    top_faces.append(simplex + len(base_coords))  # Geser indeks untuk bagian atas

            # Membuat sisi vertikal prisma
            num_points = len(base_coords)
            side_faces = []
            for i in range(num_points - 1):
                side_faces.append([i, i + 1, i + num_points])
                side_faces.append([i + 1, i + num_points + 1, i + num_points])
            
            # Menggabungkan semua faces (tutup dasar, sisi, dan tutup atas)
            faces = np.vstack((base_faces, top_faces, side_faces))
            
            # Membuat mesh dari prisma
            mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
            meshes.append(mesh)

    # Gabungkan semua prisma menjadi satu mesh
    combined_mesh = trimesh.util.concatenate(meshes)

    # Langkah 4: Menyimpan sebagai file OBJ
    combined_mesh.export(output_path)
    print(f"3D model prisma berhasil disimpan di {output_path}")
