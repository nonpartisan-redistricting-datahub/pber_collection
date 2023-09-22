import pandas as pd # standard python data library, my machine uses version 1.5.0
import geopandas as gp # the geo-version of pandas, my machine uses version 0.9.0
import numpy as np # my machine uses version 1.23.3
from matplotlib.lines import Line2D

def county_totals_check(partner_df, partner_name, source_df, source_name, column_list, county_col, full_print=False, method="race"):
    """Compares the totals of two, unjoined, election result dataframes at the county level

    Args:
      partner_df: DataFrame of election results we are comparing against
      partner_name: String of what to call the partner in the print statement
      source_df: DataFrame of election results we are comparing to
      source_name: String of what to call the source in the print statement
      column_list: List of races that there are votes for
      county_col: String of the column name that contains county information
      full_print: Boolean specifying whether to print out everything, including counties w/ similarities
      method: Accepts either "race" or "county", determines how contests are iterated over

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
                    print("\t"+val+" has a difference of "+str(county_differences[val])+" votes")
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
        
def statewide_totals_check(partner_df, partner_name, source_df, source_name, column_list):
    """Compares the totals of two election result dataframes at the statewide total level

    Args:
      partner_df: DataFrame of election results we are comparing against
      source_df: DataFrame of election results we are comparing to
      column_list: List of races that there are votes for
 
    Returns:
      Nothing, only prints out an analysis
    """
    print("***Statewide Totals Check***")
    diff_races=[]
    for race in column_list:
        if (partner_df[race].sum()- source_df[race].sum() != 0):
            if race not in diff_races:
                diff_races.append(race)
            print(race+" has a difference of "+str(partner_df[race].sum()-source_df[race].sum())+" votes")
            print("\t"+ partner_name + ": "+str(partner_df[race].sum())+" votes")
            print("\t"+ source_name +": "+str(source_df[race].sum())+" votes")
        else:
            print(race + " is equal", "\t both dataframes " + str(partner_df[race].sum()))
    if (len(diff_races)>0):
        print()
        print(diff_races)

def merged_df_votes_checks(merged_df, name_col, column_list, left_df_name, right_df_name, level_name, print_level=0):
    """Checks a merged dataframe with two election results at the precinct level

    Args:
      merged_df: DataFrame with one set of election results joined to another
      name_col: String of the column name to refer to precincts when a difference occurs
      column_list: List of races that there are votes for
      left_df_name: What to call the left DataFrame in the print out
      right_df_name: What to call the right DataFrame in the print out
      level_name: What to call the unit at which the two DataFrames are being compared
      print_level: Integer that specifies how large the vote difference must be to be printed

    Returns:
      Nothing, only prints out an analysis
    """
    merged_df = merged_df.sort_values(by=[name_col],inplace=False)
    right_df_name = "("+right_df_name+")"
    left_df_name = "("+left_df_name+")"

    matching_rows = 0
    different_rows = 0
    diff_list=[]
    diff_values = []
    max_diff = 0
    max_len = max(len(left_df_name), len(right_df_name))
    for index,row in merged_df.iterrows():
        same = True
        for i in column_list:
            left_data = i + "_x"
            right_data = i + "_y"
            if ((row[left_data] is None) or (row[right_data] is None) or (np.isnan(row[right_data])or(np.isnan(row[left_data])))):
                print("FIX NaN value at: ", row[name_col])
                return;
            diff = abs(row[left_data]-row[right_data])
            if (diff>0):
                same = False
                if (diff>max_diff):
                    max_diff = diff
            if(diff>print_level):
                diff_values.append(abs(diff))
                if row[name_col] not in diff_list:
                    diff_list.append(row[name_col])
                print(i, "{:.>62}".format(row[name_col]), "{name:>{field_size}}{data:.>5}".format(name=left_df_name, field_size = max_len, data = int(row[left_data])),"{name:>{field_size}}{data:.>5}".format(name=right_df_name, field_size = max_len, data = int(row[right_data])),"(Diff):{:>5}".format(int(row[left_data]-row[right_data])))
        if(same != True):
            different_rows +=1
        else:
            matching_rows +=1
    print("")
    print("There are ", len(merged_df.index)," total rows")
    print(different_rows," of these rows have election result differences")
    print(matching_rows," of these rows are the same")
    print("")
    print("The max difference between any one shared column in a row is: ", max_diff)
    if(len(diff_values)!=0):
        print("The average difference is: ", str(sum(diff_values)/len(diff_values)))
    count_big_diff = len([i for i in diff_values if i > 10])
    print("There are {} {} results with a difference greater than 10".format(str(count_big_diff), level_name))
    print("")
    print("All {} containing differences:".format(level_name))
    diff_list.sort()
    print(len(diff_list))
    print(diff_list)
    
    
def allocate_absentee(df_receiving_votes,df_allocating,column_list,col_allocating,allocating_to_all_empty_precs=False):
    """Allocates votes proportionally to precincts, usually by share of precinct-reported vote

    Args:
      df_receiving_votes: DataFrame with precinct-level votes
      df_allocating: DataFrame with the votes to allocate
      column_list: List of races that votes are being allocated for
      col_allocating: String referring to what level the allocation occurs at (most often county)
      allocating_to_all_empty_precs: Boolean for special case where all votes in df_receiving_votes are 0

    Returns:
      The precinct-level votes dataframe (df_receiving_votes) with the allocated votes
    """
    
    #Fill any n/a values with 0
    df_receiving_votes = df_receiving_votes.fillna(0)
    #Grab the original columns, so we can filter back down to them later
    original_cols = list(df_receiving_votes.columns)
    
    #Add in the "Total Votes column"
    if (allocating_to_all_empty_precs):
        #In cases where every vote is 0, need to set the Total_Votes equal to 1 for proportional allocation
        df_receiving_votes.loc[:,"Total_Votes"]=1
    else:
        df_receiving_votes.loc[:,"Total_Votes"]=0
        for race in column_list:
            df_receiving_votes.loc[:,"Total_Votes"]+=df_receiving_votes.loc[:,race]
    
    #Create the needed dataframes
    precinct_specific_totals = pd.DataFrame(df_receiving_votes.groupby([col_allocating]).sum())
    precinct_specific_totals.reset_index(drop=False,inplace=True)
    to_dole_out_totals = pd.DataFrame(df_allocating.groupby([col_allocating]).sum())
    to_dole_out_totals.reset_index(drop=False,inplace=True)
    
    #Add in total sum check
    sum_dataframe = pd.DataFrame(columns=precinct_specific_totals.columns)
    for i in column_list:
        total_votes = precinct_specific_totals.loc[:,i].sum()+to_dole_out_totals.loc[:,i].sum()
        sum_dataframe.at[0,i]=total_votes.astype(int)
    
    #Check the allocating to empty precincts code
    if (allocating_to_all_empty_precs):
        for i in column_list:
            if(sum(precinct_specific_totals[i])!=0):
                print("Allocating to all empty precincts parameter incorrect")
                break
    
    #Print out any instances where the allocation, as written, won't work
    special_allocation_needed = []
    for index, row in precinct_specific_totals.iterrows():
        for race in column_list:
            if (row[race]==0):
                race_district = row[col_allocating]
                if race_district in to_dole_out_totals[col_allocating].unique():
                    to_allocate = int(to_dole_out_totals.loc[to_dole_out_totals[col_allocating]==race_district][race])
                    if (to_allocate != 0):
                        special_allocation_needed.append([race_district,race])
                        if(row["Total_Votes"]==0):
                            precinct_specific_totals.loc[index,"Total_Votes"]=1
                            col_val = row[col_allocating]
                            df_receiving_votes.loc[df_receiving_votes[col_allocating]==col_val,"Total_Votes"]=1
                            special_allocation_needed.append([race_district,race])
    if(len(special_allocation_needed) > 0):
        print("Special allocation used for", special_allocation_needed)

    #Create some new columns for each of these races to deal with the allocation
    for race in column_list:
        add_var = race+"_add"
        rem_var = race+"_rem"
        floor_var = race+"_floor"
        df_receiving_votes.loc[:,add_var]=0.0
        df_receiving_votes.loc[:,rem_var]=0.0
        df_receiving_votes.loc[:,floor_var]=0.0

    #Iterate over the rows
    #Note this function iterates over the dataframe two times so the rounded vote totals match the totals to allocate
    for index, row in df_receiving_votes.iterrows():
        if row[col_allocating] in to_dole_out_totals[col_allocating].unique():
            for race in column_list:
                add_var = race+"_add"
                rem_var = race+"_rem"
                floor_var = race+"_floor"
                #Grab the district
                county_id = row[col_allocating]
                if [county_id,race] in special_allocation_needed:
                    #Get the denominator for the allocation - the summed "total votes" for precincts in that grouping
                    denom = precinct_specific_totals.loc[precinct_specific_totals[col_allocating]==county_id]["Total_Votes"]
                    #Get one of the numerators, how many districtwide votes to allocate
                    numer = to_dole_out_totals.loc[to_dole_out_totals[col_allocating]==county_id][race]
                    #Get the "total votes" for this particular precinct
                    val = df_receiving_votes.at[index,"Total_Votes"]
                    #Get the vote share, the precincts % of total precinct votes in the district times votes to allocate
                else:
                    #Get the denominator for the allocation (the precinct vote totals)
                    denom = precinct_specific_totals.loc[precinct_specific_totals[col_allocating]==county_id][race]
                    #Get one of the numerators, how many districtwide votes to allocate
                    numer = to_dole_out_totals.loc[to_dole_out_totals[col_allocating]==county_id][race]
                    #Get the vote totals for this race in this precinct
                    val = df_receiving_votes.at[index,race]
                    #Get the vote share, the precincts % of total precinct votes in the district times votes to allocate
                if ((float(denom)==0)):
                    vote_share = 0
                else:
                    vote_share = (float(val)/float(denom))*float(numer)
                df_receiving_votes.at[index,add_var] = vote_share
                #Take the decimal remainder of the allocation
                df_receiving_votes.at[index,rem_var] = vote_share%1
                #Take the floor of the allocation
                df_receiving_votes.at[index,floor_var] = np.floor(vote_share)

    #After the first pass through, get the sums of the races by district to assist in the rounding            
    first_allocation = pd.DataFrame(df_receiving_votes.groupby([col_allocating]).sum())

    #Now we want to iterate district by district to work on rounding
    county_list = list(to_dole_out_totals[col_allocating].unique()) 

    #Iterate over the district
    for county in county_list:
        for race in column_list:
            add_var = race+"_add"
            rem_var = race+"_rem"
            floor_var = race+"_floor"
            #County how many votes still need to be allocated (because we took the floor of all the initial allocations)
            to_go = int(np.round((int(to_dole_out_totals.loc[to_dole_out_totals[col_allocating]==county][race])-first_allocation.loc[first_allocation.index==county,floor_var])))
            #Grab the n precincts with the highest remainders and round these up, where n is the # of votes that still need to be allocated
            for index in df_receiving_votes.loc[df_receiving_votes[col_allocating]==county][rem_var].nlargest(to_go).index:
                df_receiving_votes.at[index,add_var] = np.ceil(df_receiving_votes.at[index,add_var])

    #Iterate over every race again
    for race in column_list:
        add_var = race+"_add"
        #Round every allocation down to not add fractional votes
        df_receiving_votes.loc[:,add_var]=np.floor(df_receiving_votes.loc[:,add_var])
        df_receiving_votes.loc[:,race]+=df_receiving_votes.loc[:,add_var]
        df_receiving_votes.loc[:,race] = df_receiving_votes.loc[:,race].astype(int)
        #Check to make sure all the votes have been allocated
        if ((sum_dataframe.loc[:,race].sum()-df_receiving_votes.loc[:,race].sum()!=0)):
            print("Some issue in allocating votes for:", i)
            
    #Filter down to original columns
    df_receiving_votes = df_receiving_votes[original_cols]

    return df_receiving_votes


def get_fips_dict(state):
    '''
    Returns a dictionary mapping from county name to FIPS for a given state.
    The state should be called with its full name
    '''
    #Load in the nationwide FIPS file
    fips_file = pd.read_csv("./raw-from-source/FIPS/US_FIPS_Codes.csv")
    fips_file = fips_file[fips_file["State"]== state]
    fips_file["FIPS County"]=fips_file["FIPS County"].astype(str)

    #Make the FIPS three digits
    fips_file["FIPS County"]=fips_file["FIPS County"].str.zfill(3)

    #Create the dictionary
    fips_dict = dict(zip(fips_file["County Name"],fips_file["FIPS County"]))
    
    return fips_dict

def compare_geometries(gdf_1,gdf_2,left_gdf_name,right_gdf_name,join_col_name, shp_names, area_threshold=.1):
    '''
    Function that joins to GeoDataFrames on a column and reports area differences row-by-row
    '''
    gdf_1 = gdf_1.to_crs(3857)
    gdf_2 = gdf_2.to_crs(3857)
    both = pd.merge(gdf_1,gdf_2,how="outer",on=join_col_name,validate="1:1",indicator=True)
    if(both["_merge"].str.contains("_")).any():
        print("Non-unique merge values")
        print(both[both["_merge"]!="both"])
        both = both[both["_merge"]=="both"]
        both.reset_index(inplace = True, drop = True)
    left_geoms = gp.GeoDataFrame(both,geometry="geometry_x")
    right_geoms = gp.GeoDataFrame(both,geometry="geometry_y")
    left_geoms["geometry_x"]=left_geoms.buffer(0)
    right_geoms["geometry_y"]=right_geoms.buffer(0)
    count = 0
    area_list = []
    print("Checking " + str(both.shape[0])+" " + shp_names + " for differences of greater than "+str(area_threshold)+" km^2")
    print()
    for index,row in both.iterrows():
        diff = left_geoms.iloc[[index]].symmetric_difference(right_geoms.iloc[[index]])
        intersection = left_geoms.iloc[[index]].intersection(right_geoms.iloc[[index]])
        area = float(diff.area/10e6)
        area_list.append(area)
        if (area > area_threshold):
            count += 1
            name = left_geoms.at[index,join_col_name]
            print(str(count)+") For " + name + " difference in area is " + str(area))
            if (intersection.iloc[0].is_empty):
                base = left_geoms.iloc[[index]].plot(color="orange",figsize=(10,10))
                right_geoms.iloc[[index]].plot(color="blue",ax=base)
                base.set_title(name)
                custom_lines = [Line2D([0], [0], color='green', lw=4),
                Line2D([0], [0], color='orange', lw=4),
                Line2D([0], [0], color='blue', lw=4)]
                base.legend(custom_lines, ['Overlap', left_gdf_name,right_gdf_name])
            else:
                base = left_geoms.iloc[[index]].plot(color="orange",figsize=(10,10))
                right_geoms.iloc[[index]].plot(color="blue",ax=base)
                intersection.plot(color="green",ax=base)
                base.set_title(name)
                custom_lines = [Line2D([0], [0], color='green', lw=4),
                Line2D([0], [0], color='orange', lw=4),
                Line2D([0], [0], color='blue', lw=4)]
                base.legend(custom_lines, ['Overlap', left_gdf_name,right_gdf_name])
                
                
    df = pd.DataFrame(area_list)
    print()
    print("Scroll down to see plots of any differences")
    print()
    print("Of the "+ str(both.shape[0])+" "+ shp_names +":")
    print()
    print(str(len(df[df[0]==0]))+" " + shp_names + " w/ a difference of 0 km^2")
    print(str(len(df[(df[0]<.1) & (df[0]>0)]))+" " + shp_names + " w/ a difference between 0 and .1 km^2")
    print(str(len(df[(df[0]<.5) & (df[0]>=.1)]))+" " + shp_names + " w/ a difference between .1 and .5 km^2")
    print(str(len(df[(df[0]<1) & (df[0]>=.5)]))+" " + shp_names + " w/ a difference between .5 and 1 km^2")
    print(str(len(df[(df[0]<2) & (df[0]>=1)]))+" " + shp_names + " w/ a difference between 1 and 2 km^2")
    print(str(len(df[(df[0]<5) & (df[0]>=2)]))+" " + shp_names + " w/ a difference between 2 and 5 km^2")
    print(str(len(df[(df[0]>=5)]))+" " + shp_names + " w/ a difference greater than 5 km^2")


def generate_differences_df(df_compare_against, df_compare_to, unique_ID_col, races_list, drop_empty=False):
    df_compare_against = df_compare_against[[unique_ID_col] + races_list]
    df_compare_to = df_compare_to[[unique_ID_col] + races_list]

    grouped_compare_against = df_compare_against.groupby(unique_ID_col).sum()
    grouped_compare_to = df_compare_to.groupby(unique_ID_col).sum()

    grouped_compare_against.reset_index(inplace=True, drop=False)
    grouped_compare_to.reset_index(inplace=True, drop=False)

    diffs = grouped_compare_against.set_index(unique_ID_col).subtract(grouped_compare_to.set_index(unique_ID_col))

    diffs["Tot_Votes"] = diffs[races_list].sum(axis=1)

    if drop_empty:
        diffs = diffs.loc[~(diffs == 0).all(axis=1)]
        diffs = diffs.loc[:, (diffs != 0).any(axis=0)]

    return diffs


def district_splits_comb(level, splits_list, elections_gdf, district_gdf, unique_ID_col, district_gdf_ID, races_list,
                         elections_gdf_dist_ID, fill_level=2):
    '''
    Function to split precincts across districts that splits a precinct across the entire district map.
    Previous iterations of this code only split precincts by the districts in which votes were recorded.
    In some instances, that led to holes in the map, due to districts where no votes were recorded in a precinct, but where an intersection occurred.
    '''
    # Intersect the elections gdf with the district gdf
    need_splits = elections_gdf[elections_gdf[unique_ID_col].isin(splits_list)]
    others = elections_gdf[~elections_gdf[unique_ID_col].isin(splits_list)]

    pre_splits_copy = need_splits.copy(deep=True)

    test_join = gp.overlay(need_splits, district_gdf, how="intersection")

    # Assign a district column, using the district shapefile
    test_join[elections_gdf_dist_ID] = test_join[district_gdf_ID]

    # Filter the intersection down to the precinct, district pairs we need
    clean_votes = test_join.copy(deep=True)

    clean_votes[unique_ID_col + "_new"] = clean_votes[unique_ID_col]

    # Remove the others and hold on to these to be merged later
    for index, row in clean_votes.iterrows():
        clean_votes.at[index, unique_ID_col + "_new"] = row[unique_ID_col] + "-(" + level + "-" + row[
            district_gdf_ID].zfill(fill_level) + ")"
        for column in test_join:
            if column in races_list and row[elections_gdf_dist_ID].zfill(fill_level) not in column:
                clean_votes.at[index, column] = 0

    lost_votes_df = generate_differences_df(pre_splits_copy, clean_votes, unique_ID_col, races_list, True)

    clean_votes.drop(unique_ID_col, axis=1, inplace=True)
    clean_votes.rename(columns={unique_ID_col + "_new": unique_ID_col}, inplace=True)

    clean_votes = clean_votes[list(others.columns)]

    elections_gdf = gp.GeoDataFrame(pd.concat([clean_votes, others]), crs=elections_gdf.crs)
    elections_gdf.reset_index(drop=True, inplace=True)

    return elections_gdf, lost_votes_df