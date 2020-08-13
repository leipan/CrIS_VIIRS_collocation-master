import numpy as np
import glob
import geo
import time
import pdb
import os,sys

start_time = time.time()

### dataDir1='/peate_archive/.data5/Ops/npp/noaa/op/2012/05/15/scris/'
### dataDir2='/peate_archive/.data5/Ops/npp/noaa/op/2012/05/15/gcrso/'
### dataDir2='/peate_archive/.data6/Ops/snpp/gdisc/2/2015/06/01/crisl1b/'
### dataDir3='/peate_archive/.data5/Ops/npp/noaa/op/2012/05/15/svm15/'
### dataDir4='/peate_archive/.data5/Ops/npp/noaa/op/2012/05/15/gmodo/'
### dataDir4='/raid15/qyue/VIIRS/VIIRS/20150601/'


### dataDir2='/tmp/data/Ops/snpp/gdisc/2/2015/06/01/crisl1b/'
dataDir2='./'
### dataDir4='/tmp/data/VIIRS/20150601/'
dataDir4='./'

# get CrIS files 
### cris_sdr_files = sorted(glob.glob(dataDir1+'SCRIS*d2012*'))[21:40]
### cris_geo_files = sorted(glob.glob(dataDir2+'GCRSO*d2012*'))[21:40]
cris_geo_files = sorted(glob.glob(dataDir2+'SNDR*1809042004*'))
print ('cris_geo_files: ', cris_geo_files)

# get VIIRS files 
### viirs_sdr_files = sorted(glob.glob(dataDir3+'SVM15*d2012*'))[31:59]
### viirs_geo_files = sorted(glob.glob(dataDir4+'GMODO*d2012*'))[31:59]
viirs_geo_files = sorted(glob.glob(dataDir4+'VNP03MOD*201726106455*'))
print ('viirs_geo_files: ', viirs_geo_files)

# read VIIRS data 
### viirs_lon, viirs_lat, viirs_satAzimuth, viirs_satRange, viirs_satZenith = geo.read_viirs_geo(viirs_geo_files)
### no need! viirs_bt, viirs_rad, viirs_sdrQa = geo.read_viirs_sdr(viirs_sdr_files)

viirs_lon, viirs_lat, viirs_satAzimuth, viirs_satRange, viirs_satZenith = geo.nc_read_viirs_geo(viirs_geo_files)
print ('viirs_lon: ', viirs_lon)
print ('viirs_lat: ', viirs_lat)
print ('viirs_satAzimuth: ', viirs_satAzimuth)
print ('viirs_satRange: ', viirs_satRange)
print ('viirs_satZenith: ', viirs_satZenith)

# read CrIS data 
### cris_lon, cris_lat, cris_satAzimuth, cris_satRange, cris_satZenith = geo.read_cris_geo(cris_geo_files)
cris_lon, cris_lat, cris_satAzimuth, cris_satRange, cris_satZenith = geo.nc_read_cris_geo(cris_geo_files)
print ('cris_lon: ', cris_lon)
print ('cris_lat: ', cris_lat)
print ('cris_satAzimuth: ', cris_satAzimuth)
print ('cris_satRange: ', cris_satRange)
print ('cris_satZenith: ', cris_satZenith)

### no need cris_realLW, cris_realMW, cris_realSW, cris_sdrQa, cris_geoQa, cris_dayFlag = geo.read_cris_sdr(cris_sdr_files , sdrFlag=True)

# compute CrIS Pos Vector in EFEC on the Earth Surface 
cris_pos= np.zeros(np.append(cris_lat.shape, 3))
cris_pos[:, :, :, 0], cris_pos[:, :, :, 1], cris_pos[:, :, :, 2] \
    = geo.LLA2ECEF(cris_lon, cris_lat, np.zeros_like(cris_lat))

# compute CrIS LOS Vector in ECEF 
cris_east, cris_north, cris_up = geo.RAE2ENU(cris_satAzimuth, cris_satZenith, cris_satRange)

cris_los= np.zeros(np.append(cris_lat.shape, 3))
cris_los[:, :, :, 0], cris_los[:, :, :, 1], cris_los[:, :, :, 2] = \
    geo.ENU2ECEF(cris_east, cris_north, cris_up, cris_lon, cris_lat)

# compute viirs POS vector in ECEF
viirs_pos= np.zeros(np.append(viirs_lat.shape, 3))
viirs_pos[:, :, 0], viirs_pos[:, :, 1], viirs_pos[:, :, 2] = \
    geo.LLA2ECEF(viirs_lon, viirs_lat, np.zeros_like(viirs_lat))

# cris_los is pointing from pixel to satellite, we need to
#   change from satellite to pixel
cris_los = -1.0*cris_los

# using Kd-tree to find the closted pixel of VIIRS for each CrIS FOV
# Set fake viirs_sdrQa to be zero: good quality everywhere since not for calibration
viirs_sdrQa=np.zeros(viirs_lon.shape)
dy, dx = geo.match_cris_viirs(cris_los, cris_pos, viirs_pos, viirs_sdrQa)
### print("collocation are done in --- %s seconds --- for %d files " % (time.time() - start_time, len(cris_sdr_files)))
print("collocation are done in --- %s seconds --- " % (time.time() - start_time))

# collocation is done

sys.exit(0)


##############################################################################
# showing the collocated images 
#############################################################################
start_time = time.time()

import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import matplotlib.colors as colors
import matplotlib.cm as cmx

print(cris_lon.min(),cris_lat.min(),cris_lon.max(),cris_lat.max())

m = Basemap(resolution='l', projection='cyl',  \
		llcrnrlon=cris_lon.min(), llcrnrlat=cris_lat.min(),  
        urcrnrlon=cris_lon.max(), urcrnrlat=cris_lat.max())
m.drawcoastlines()
m.drawcountries()
m.drawstates()

# meridians on bottom and left
parallels = np.arange(0.,81,10.)
m.drawparallels(parallels,labels=[False,True,True,False])
meridians = np.arange(10.,351.,20.)
m.drawmeridians(meridians,labels=[True,False,False,True])

# create color map 
jet = cm = plt.get_cmap('jet') 
cNorm  = colors.Normalize(vmin=220, vmax=310)
scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)

# show collocated pixels 
for k, j, i in np.ndindex(cris_lat.shape):
	
	ix=dx[k,j,i]
	iy=dy[k,j,i]
	vcolorVal = np.squeeze(scalarMap.to_rgba(viirs_bt[iy, ix]))
	vx, vy = m(viirs_lon[iy, ix], viirs_lat[iy, ix])
	cs1 = m.scatter(vx, vy, s=0.5, c=vcolorVal, edgecolor='none', cmap='jet', marker='.')

plt.savefig('myfig_20190219', dpi=300)    

print("making plots is using --- %s seconds " % (time.time() - start_time))



 
