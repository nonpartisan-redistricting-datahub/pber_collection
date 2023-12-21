import geopandas as gp
import pandas as pd
import os
import numpy as np
import re
from collections import Counter

def district_splits_mod(cd_list, level, old_name, elections_gdf, shps_gdf, unique_ID_col, district_ID, races_list, dist_column):
    '''
    Function to split precincts across districts that splits a precinct across the entire district map.
    Previous iterations of this code only split precincts by the districts in which votes were recorded.
    In some instances, that led to holes in the map, due to districts where no votes were recorded in a precinct, but where an intersection occurred.
    '''
    full_shape = elections_gdf.loc[elections_gdf[unique_ID_col]==old_name]    
    test_join = gp.overlay(full_shape, shps_gdf, how = "intersection")
    test_join[dist_column] = test_join[district_ID]
    if test_join.empty:
        print("***Issue merging district ", old_name)
    for index, row in test_join.iterrows():
        test_join.at[index, unique_ID_col] = old_name+"-("+level + "-" + row[district_ID] + ")"
        for column in test_join:
            if column in races_list and row[district_ID] not in column:
                test_join.at[index, column] = 0 
        test_join = test_join[list(elections_gdf.columns)]
    elections_gdf=elections_gdf[elections_gdf[unique_ID_col]!=old_name]
    elections_gdf = pd.concat([elections_gdf, test_join])
    elections_gdf.reset_index(drop=True,inplace=True)
    return elections_gdf

def is_split_precinct(district_assignment_list):
    c = Counter([x[0] for x in district_assignment_list])
    greater_than_one = {x:[y[1] for y in district_assignment_list if y[0]==x] for x, count in c.items() if count > 1}
    if len(greater_than_one)==0:
        return 0
    else:
        return greater_than_one
    
def get_level_dist(column_name):
    if column_name[0:3] == "PSL":
        level = "SL"
        dist = column_name[3:5]
    elif column_name[0:3] == "PSU":
        level = "SU"
        dist = column_name[3:5]
    elif column_name[0:4] == "PCON":
        level = "CON"
        dist = column_name[4:6]
    else:
        print(column_name)
        raise ValueError
    return level,dist

def contains_sldl(dist_list):
    for dist_tuple in dist_list:
        if dist_tuple[0] == "SL":
            return dist_tuple[1]
        
def contains_cong(dist_list):
    for dist_tuple in dist_list:
        if dist_tuple[0] == "CON":
            return dist_tuple[1]
        
def contains_sldu(dist_list):
    for dist_tuple in dist_list:
        if dist_tuple[0] == "SU":
            return dist_tuple[1]
        
def return_cd(row, races_list):
    for val in races_list:
        if row[val] != 0:
            return val[4:6]
        
def return_sl(row, races_list):
    for val in races_list:
        if row[val] != 0:
            return val[3:5]

def county_totals_check(partner_df, partner_name, source_df, source_name, column_list, county_col, full_print=False, method="race"):
    """Compares the totals of two election result dataframes at the county level

    Args:
      partner_df: DataFrame of election results we are comparing against
      partner_name: String of what to call the partner in the print statement
      source_df: DataFrame of election results we are comparing to
      source_name: String of what to call the source in the print statement
      column_list: List of races that there are votes for
      county_col: String of the column name that contains county information
      full_print: Boolean specifying whether to print out everything, including counties w/ similarities

    Returns:
      Nothing, only prints out an analysis
    """
    
    print("***Countywide Totals Check***")
    print("")
    
    if method == "race":
        diff_counties=[]
        for race in column_list:
            diff = partner_df.groupby([county_col]).sum()[race]-source_df.groupby([county_col]).sum()[race]
            for val in diff[diff != 0].index.values.tolist():
                if val not in diff_counties:
                    diff_counties.append(val)
            if len(diff[diff != 0]!=0):   
                print(race + " contains differences in these counties:")
                for val in diff[diff != 0].index.values.tolist():
                    county_differences = diff[diff != 0]
                    print("\t"+val+" has a difference of "+(county_differences[val])+" votes")
                    print("\t\t"+ partner_name + ": "+str(partner_df.groupby([county_col]).sum().loc[val,race])+" votes")
                    print("\t\t"+ source_name +": "+str(source_df.groupby([county_col]).sum().loc[val,race])+" votes")
                if (full_print):
                    for val in diff[diff == 0].index.values.tolist():
                        county_similarities = diff[diff == 0]
                        print("\t"+val + ": "+ str(partner_df.groupby([county_col]).sum().loc[val,race])+" votes")
            else:
                print(race + " is equal across all counties")
                if (full_print):
                    for val in diff[diff == 0].index.values.tolist():
                        county_similarities = diff[diff == 0]
                        print("\t"+val + ": "+ str(partner_df.groupby([county_col]).sum().loc[val,race])+" votes")
        if (len(diff_counties)>0):
            print()
            diff_counties.sort()
            print(diff_counties)
    elif method == "county":
        if set(source_df[county_col].unique()) != set(partner_df[county_col].unique()):
            raise ValueError("Not all counties will be checked")
        diff_counties=[]
        good_counties=[]
        holder_1 = partner_df.groupby(county_col).sum()
        holder_2 = source_df.groupby(county_col).sum()
        for county in list(partner_df[county_col].unique()):
            no_diff = True
            for race in column_list:
                partner_val = holder_1.loc[county][race]
                source_val =  holder_2.loc[county][race]
                diff = partner_val - source_val
                if diff != 0:
                    if no_diff:
                        print(f"{county} contains differences in these races:")
                        no_diff = False
                    print(f"\t{race} has a difference of {diff} vote(s)")
                    print(f"\t\t{partner_name}: {partner_val} vote(s)")
                    print(f"\t\t{source_name}: {source_val} vote(s)")
            if no_diff:
                good_counties.append(county)
            else:
                diff_counties.append(county)
        if (len(diff_counties)>0):
            print()
            diff_counties.sort()
            print(diff_counties)
        print("Counties that match:")
        if (len(good_counties)>0):
            print()
            good_counties.sort()
            print(good_counties)
    else:
        raise ValueError("Enter a correct method: race or county")

