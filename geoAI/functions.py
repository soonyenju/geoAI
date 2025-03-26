from matplotlib import pyplot as plt

def show_city_boundary(shp, country, buffer = 0.1, fc = '#ff7f0e'):
    shp.plot()
    ax = plt.gca()
    country.plot(ax = ax, fc = '#1f77b4', alpha = 0.2)
    ax.set_xlim(shp.bounds.minx.item() - buffer, shp.bounds.maxx.item() + buffer)
    ax.set_ylim(shp.bounds.miny.item() - buffer, shp.bounds.maxy.item() + buffer)
    return ax
    

