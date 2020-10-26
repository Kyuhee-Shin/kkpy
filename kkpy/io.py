"""
kkpy.io
========================

Functions to read and write files

.. currentmodule:: io

.. autosummary::
    kkpy.io.read_aws
    kkpy.io.read_2dvd_rho
    kkpy.io.read_mxpol_rhi_with_hc
    kkpy.io.read_dem

"""
import numpy as np
import datetime
import glob
import scipy.io
import pyart
import wradlib as wrl

def read_aws(time=None, datadir='/disk/STORAGE/OBS/AWS/', date_range=True):
    """
    Read AWS_MIN files into dataframe.
    
    Examples
    ---------
    >>> import datetime
    >>> df_aws = kkpy.io.read_aws(time=datetime.datetime(2018,2,28,6,0))
    
    >>> df_aws = kkpy.io.read_aws(time=[datetime.datetime(2018,2,28,6,0),datetime.datetime(2018,3,1,12,0)], datadir='/path/to/aws/files/')
    
    Parameters
    ----------
    time : datetime or array_like of datetime
        Datetime of the data you want to read.
        If this is array of two elements, it will read all data within two datetimes by default.
        If this is array of elements and keyword *range* is False, it will read the data of specific time of each element.
    datadir : str, optional
        Directory of the data.
    date_range : bool, optional
        False if argument *time* contains element of specific time you want to read.
        
    Returns
    ---------
    df_aws : dataframe
        Return dataframe of aws data.
    """
    
    list_aws = []
    
    filearr_1d = np.sort(glob.glob(aws_dir+YYYYMMDD[:6]+'/'+YYYYMMDD[6:8]+'/'+'AWS_MIN_'+YYYYMMDD+'*'))
    for file in filearr_1d:
        data = pd.read_csv(file, delimiter='#', names=names)
        data.wd         = data.wd/10.
        data.ws         = data.ws/10.
        data.t          = data.t/10.
        data.rh         = data.rh/10.
        data.pa         = data.pa/10.
        data.ps         = data.ps/10.
        data.rn60m_acc  = data.rn60m_acc/10.
        data.rn1d       = data.rn1d/10.
        data.rn15m      = data.rn15m/10.
        data.rn60m      = data.rn60m/10.
        data.wds        = data.wds/10.
        data.wss        = data.wss/10.
        list_aws.append(data[data.stn == 100].values.tolist()[0])

    df_aws = pd.DataFrame(list_aws, columns=names)
    
    
    return df_aws



def read_2dvd_rho(time=None, datadir='/disk/STORAGE/OBS/AWS/', date_range=True):
    """
    Read AWS_MIN files into dataframe.
    
    Examples
    ---------
    >>> import datetime
    >>> df_aws = kkpy.io.read_aws(time=datetime.datetime(2018,2,28,6,0))
    
    >>> df_aws = kkpy.io.read_aws(time=[datetime.datetime(2018,2,28,6,0),datetime.datetime(2018,3,1,12,0)], datadir='/path/to/aws/files/')
    
    Parameters
    ----------
    time : datetime or array_like of datetime
        Datetime of the data you want to read.
        If this is array of two elements, it will read all data within two datetimes by default.
        If this is array of elements and keyword *range* is False, it will read the data of specific time of each element.
    datadir : str, optional
        Directory of the data.
    date_range : bool, optional
        False if argument *time* contains element of specific time you want to read.
        
    Returns
    ---------
    df_aws : dataframe
        Return dataframe of aws data.
    """
    # Get file list
    filearr = np.array(np.sort(glob.glob(f'{datadir}/**/2DVD_Dapp_v_rho_201*Deq.txt', recursive=True)))
    yyyy_filearr = [np.int(os.path.basename(x)[-27:-23]) for x in filearr]
    mm_filearr = [np.int(os.path.basename(x)[-23:-21]) for x in filearr]
    dd_filearr = [np.int(os.path.basename(x)[-21:-19]) for x in filearr]
    dt_filearr = np.array([datetime.datetime(yyyy,mm,dd) for (yyyy, mm, dd) in zip(yyyy_filearr, mm_filearr, dd_filearr)])

    # Select file within time range
    if ((len(time) == 2) & date_range):
        dt_start = time[0]
        dt_finis = time[1]
        # dt_start = datetime.datetime(2017,12,24)
        # dt_finis = datetime.datetime(2017,12,25)
        filearr = filearr[(dt_filearr >= dt_start) & (dt_filearr < dt_finis)]
        dt_filearr = dt_filearr[(dt_filearr >= dt_start) & (dt_filearr < dt_finis)]
    
    
    # # READ DATA
    columns = ['hhmm', 'Dapp', 'VEL', 'RHO', 'AREA', 'WA', 'HA', 'WB', 'HB', 'Deq']
    dflist = []
    for i_file, (file, dt) in enumerate(zip(filearr, dt_filearr)):
        _df = pd.read_csv(file, skiprows=1, names=columns, header=None, delim_whitespace=True)
        _df['year'] = dt.year
        _df['month'] = dt.month
        _df['day'] = dt.day
        _df['hour'] = np.int_(_df['hhmm'] / 100)
        _df['minute'] = _df['hhmm'] % 100
        _df['jultime'] = pd.to_datetime(_df[['year','month','day','hour','minute']])
        _df['jultime_minute'] = _df['jultime']
        _df = _df.drop(['hhmm','year','month','day','hour','minute'], axis=1)
        _df = _df.drop(['Dapp', 'RHO', 'WA', 'HA', 'WB', 'HB'], axis=1)
        dflist.append(_df)
        print(i_file+1, filearr.size, file)

    df_2dvd_drop = pd.concat(dflist, sort=False, ignore_index=True)
    df_2dvd_drop.set_index('jultime', inplace=True)

    return df_2dvd_drop


def read_mxpol_rhi_with_hc(rhifile_nc, hcfile_mat):
    """
    Read MXPOL RHI with hydrometeor classification into py-ART radar object.
    
    Examples
    ---------
    >>> radar_mxp = kkpy.io.read_mxpol_rhi_with_hc(glob.glob('/path/to/rhi/*.nc'), glob.glob('/path/to/hc/*.mat'))
    
    Parameters
    ----------
    rhifile_nc : str or array_like of str
        Filepath of RHI data to read.
        The number and the order of elements should match with `hcfile_mat`.
    hcfile_mat : str or array_like of str
        Filepath of hydrometeor classification file to read.
        The number and the order of elements should match with `rhifile_nc`.
        
    Returns
    ---------
    radar : py-ART radar object
        Return py-ART radar object.
    """
    # HC file
    HC_proportion = scipy.io.loadmat(hcfile_mat)
    # RHI file
    mxpol = Dataset(rhifile_nc,'r')
    El = mxpol.variables['Elevation'][:]
    wh_hc = np.logical_and(El>5,El<175)
    El = El[wh_hc]
    R = mxpol.variables['Range'][:]

    radar = pyart.testing.make_empty_rhi_radar(HC_proportion['AG'].shape[1], HC_proportion['AG'].shape[0], 1)

    ######## HIDs ########
    # find most probable habit
    for i, _HC in HC_proportion.items():
        if '_' in i: continue
            
        if i in 'AG':
            HC3d_proportion = np.array(HC_proportion[i])
        else:
            HC3d_proportion = np.dstack([HC3d_proportion, HC_proportion[i]])
    HC = np.float_(np.argmax(HC3d_proportion, axis=2))
    HC[np.isnan(HC3d_proportion[:,:,0])] = np.nan
    
    # add to PYART radar fields
    list_str = [
        'AG', 'CR', 'IH',
        'LR', 'MH', 'RN',
        'RP', 'WS']
    list_standard = [
        'Aggregation', 'Crystal', 'Ice hail / Graupel',
        'Light rain', 'Melting hail', 'Rain',
        'Rimed particles', 'Wet snow']
    for _str, _standard in zip(list_str, list_standard):
        mask_dict = {
            'data':HC_proportion[_str], 'unit':'-',
            'long_name':f'Proportion of the {_str}',
            '_FillValue':-9999, 'standard_name':_standard}
        radar.add_field(_str, mask_dict, replace_existing=True)
    
    radar.add_field('HC',
                    {'data':HC, 'unit':'-',
                     'long_name':f'Most probable habit. AG(0), CR(1), IH(2), LR(3), MH(4), RN(5), RP(6), WS(7)',
                     '_FillValue':-9999, 'standard_name':'Hydrometeor classification'},
                    replace_existing=True)
    
    ######## Radar variables ########
    ZDR = mxpol.variables['Zdr'][:].T[wh_hc]
    Z   = mxpol.variables['Zh'][:].T[wh_hc]
    KDP = mxpol.variables['Kdp'][:].T[wh_hc]

    mask_dict = {
        'data':KDP, 'unit':'deg/km',
        'long_name': 'differential phase shift',
        '_FillValue':-9999, 'standard_name':'KDP'
    }
    radar.add_field('KDP', mask_dict)

    mask_dict = {
        'data':ZDR-4.5, 'unit':'dB',
        'long_name': 'differential reflectivity',
        '_FillValue':-9999, 'standard_name':'ZDR'
    }
    radar.add_field('ZDR', mask_dict)

    mask_dict = {
        'data':Z, 'unit':'dBZ',
        'long_name': 'horizontal reflectivity',
        '_FillValue':-9999, 'standard_name':'ZHH'
    }
    radar.add_field('ZHH', mask_dict)


    radar.range['data'] = R
    radar.elevation['data'] = El
    azimuth = np.array(mxpol['Azimuth'][:][wh_hc])
    if azimuth[0] < 0: azimuth += 360
    radar.azimuth['data'] = azimuth
    radar.fixed_angle['data'] = azimuth
    radar.time['data'] = np.array(mxpol.variables['Time'][:])
    radar.time['units'] = "seconds since 1970-01-01T00:00:00Z"
    radar.longitude['data'] = np.array([mxpol.getncattr('Longitude-value')])
    radar.latitude['data'] = np.array([mxpol.getncattr('Latitude-value')])
    radar.metadata['instrument_name'] = 'MXPol'
    radar.altitude['data'] = np.array([mxpol.getncattr('Altitude-value')])
    
    return radar

def read_dem(file=None, area='pyeongchang'):
    """
    Read NASA SRTM 3-arcsec (90 meters) digital elevation model in South Korea.
    
    Examples
    ---------
    >>> dem, lon_dem, lat_dem, proj_dem = kkpy.io.read_dem(area='pyeongchang')
    >>> ax = plt.subplot(projection=ccrs.PlateCarree())
    >>> pm = ax.pcolormesh(lon_dem, lat_dem, dem.T, cmap=cmap, vmin=0, transform=ccrs.PlateCarree())
    
    >>> dem, lon_dem, lat_dem, proj_dem = kkpy.io.read_dem(area='korea')
    
    >>> dem, lon_dem, lat_dem, proj_dem = kkpy.io.read_dem(file='./pyeongchang_90m.tif')
    
    Parameters
    ----------
    file : str, optional
        Filepath of .tif DEM file to read.
    area : str, optional
        Region of interest. Possible options are 'pyeongchang' and 'korea'. Default is 'pyeongchang'.
        
    Returns
    ---------
    dem : float array
        Return DEM elevation.
    lon_dem : float array
        Return longitude of each DEM pixel.
    lat_dem : float array
        Return latitude of each DEM pixel.
    proj_dem : osr object
        Spatial reference system of the used coordinates.
    """
    
    if file is not None:
        ds = wrl.io.open_raster(file)
    else:
        if area in 'pyeongchang':
            ds = wrl.io.open_raster('/disk/WORKSPACE/kwonil/SRTM3_V2.1/TIF/pyeongchang_90m.tif')
        elif area in 'korea':
            ds = wrl.io.open_raster('/disk/WORKSPACE/kwonil/SRTM3_V2.1/TIF/korea_90m.tif')
        else:
            print('Please check area argument')
            
    dem, coord, proj_dem = wrl.georef.extract_raster_dataset(ds)
    lon_dem = coord[:,:,0]
    lat_dem = coord[:,:,1]
    dem = dem.astype(float)
    dem[dem <= 0] = np.nan
    dem = dem.T

    return dem, lon_dem, lat_dem, proj_dem