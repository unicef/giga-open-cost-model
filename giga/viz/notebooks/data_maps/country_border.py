import geopandas as gpd


class CountryBorder:
    """
    Class for loading and accessing country borders
    """

    def __init__(self, borders):
        # borders is a geopandas dataframe
        self.borders = borders

    @staticmethod
    def from_shapefile(shapefile):
        borders = gpd.read_file(shapefile)
        borders['NAME'] = borders['NAME'].apply(lambda x: x.lower())
        return CountryBorder(borders)

    def get_border(self, country):
        # sample country has rwanda border
        country_id = 'rwanda' if country == 'sample' else country
        country_id = country_id.replace("_", " ")
        return self.borders[self.borders["NAME"] == country_id]