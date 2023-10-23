import geopandas as gp
import pandas as pd
import os
import numpy as np
import re

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

#Function cleans candidate and contest strings, and combines into a pivot column
def create_pivot_col(df, name_string, contest_string, party_string, pivot_string):
    df[name_string] = df[name_string].apply(lambda x: str(x).strip()).copy()
    df[contest_string] = df[contest_string].apply(lambda x: str(x).strip()).copy()
    df[name_string] = df[name_string].apply(lambda x:' '.join(str(x).split())).copy() # This removes extra spaces between first and last name
    substrings_to_remove = ['.', "'", '"', ',']
    for substring in substrings_to_remove:
        df[name_string] = df[name_string].apply(lambda x: x.replace(substring, '')).copy()
        df[contest_string] = df[contest_string].apply(lambda x: x.replace(substring, '')).copy()
    #Anomalies specific to this election
    df[name_string] = df[name_string].apply(lambda x: str(x).strip()).copy()
    df[contest_string] = df[contest_string].apply(lambda x: str(x).strip()).copy()
    df[pivot_string]= df[contest_string]+ ' -:- ' + df[name_string]+ ' -:- ' + df[party_string]
    return df

def get_VEST(name_string):
    electype = get_election_type_year(name_string)
    party = get_party(name_string.split("-:-")[-1])
    contest = get_race(name_string)
    candidate = get_name(name_string)
    if "CONSTITUTION" in name_string or "STATEWIDE AMENDMENT" in name_string:
        new_col_name = electype + contest + candidate
    else:
        new_col_name = electype + contest + party + candidate
    if len(new_col_name) > 10:
        print(name_string)
        print(new_col_name)
    return new_col_name

def create_column_rename_dicts(df, exclude_columns):
    contest_columns = [i for i in df.columns if i not in exclude_columns]

    contest_updates_dict = {}
    contest_updates_reversed = {}
    clean_dups = {}
    new_names = []
    
    for val in contest_columns:
        new_name = get_VEST(val)  # get_VEST
        contest_updates_dict[val] = new_name
        
        if new_name not in new_names:
            new_names.append(new_name)
            contest_updates_reversed[new_name] = val
        else:
            print("Duplicate", new_name)
            print(contest_updates_reversed[new_name])
            print(val)
            clean_dups[val] = contest_updates_reversed[new_name]
    
    return contest_updates_dict, contest_updates_reversed, clean_dups

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

def get_race(race_string):
    race_string = race_string.lower().strip()
    if 'board of education' in race_string or 'boe' in race_string:
        district = ''.join(filter(str.isdigit, race_string)).zfill(2)
        return "BOE" + district
    elif "united states representative" in race_string or 'us house' in race_string or "us congress" in race_string:
        district = ''.join(filter(str.isdigit, race_string)).zfill(2)
        return "CON" + district
    elif "united states senator" in race_string:
        return "USS"
    elif "state house" in race_string or "state representative" in race_string or 'al house' in race_string:
        district = ''.join(filter(str.isdigit, race_string)).zfill(3)
        return "SL" + district
    elif "state senator" in race_string or 'al senate' in race_string:
        district = ''.join(filter(str.isdigit, race_string)).zfill(2)
        return "SU" + district
    elif "us senate" in race_string or "us senate" in race_string:
        return "USS"
    elif "public service" in race_string or 'psc' in race_string:
        if "1" in race_string:
            return "PS1"
        elif "2" in race_string:
            return "PS2"
    elif "attorney general" in race_string:
        return "ATG"
    elif 'state auditor' in race_string or 'auditor' in race_string:
        return "AUD"
    elif "treasurer" in race_string:
        return "TRE"
    elif "secretary of state" in race_string:
        return "SOS"
    elif "lieutenant governor" in race_string:
        return "LTG"
    elif "governor" in race_string or 'govenor' in race_string:
        return "GOV"
    elif "commissioner Of labor" in race_string:
        return "LAB"
    elif "agriculture" in race_string:
        return "AGR"
    elif "commissioner of insurance" in race_string:
        return "INS"
    elif "supreme court" in race_string:
        if "5" in race_string:
            return "SSC5"
        elif "6" in race_string:
            return "SSC6"
    elif "constitution" in race_string:
        return "CNS"
    elif "amendment" in race_string:
        if "one " in race_string:
            return "A01"
        elif "two " in race_string:
            return "A02"
        elif "three " in race_string:
            return "A03"
        elif "four " in race_string:
            return "A04"
        elif "five' " in race_string:
            return "A05"
        elif "six " in race_string:
            return "A06"
        elif "seven " in race_string:
            return "A07"
        elif "eight " in race_string:
            return "A08"
        elif "nine " in race_string:
            return "A09"
        elif "ten " in race_string:
            return "A10"
        else:
            print("NO RACE", race_string)
            return ""
   
        
def get_election_type_year(race_string):
    electype = "R"
    if 'amendment' in race_string.lower():
        electype = 'G'
    if any(word in race_string.lower() for word in ['al house', 'us congress', 'al senate', 'us house', 'state house', 'state senate', 'boe', 'board of education', 'supreme court', 'united states representative', 'state representative', 'state senator']):
        return electype
    else:
        return electype +"22"
        
def get_party(race_string):
    if "REP" in race_string:
        return "R"
    elif "DEM" in race_string or "(Democrat)" in race_string:
        return "D"
    elif "LIB" in race_string or "(L)" in race_string:
        return "L"
    elif "NON" in race_string:
        return "O"
    elif "IND" in race_string:
        return "I"
    elif race_string[0:3]=="Yes":
        return "YES"
    elif race_string[0:2]=="No":
        return "NO"
    else:
        print("NO RACE", race_string)
        return ""
           
def get_name(race_string):
    name_string = race_string.split("-:-")[1]
    #print('Split string', name_string)
    name_string = name_string.replace("'","")
    name_string = name_string.replace(',','')
    name_string = name_string.strip()
    likely_last = name_string.split(" ")[-1]
    #print('likely last', likely_last)
    proposed_last = likely_last[:3]
    #print('proposed last if no suffix', proposed_last)
    if proposed_last in ['II', 'III', 'Jr', 'Jr.', 'Sr.', 'JR.', "JR", "IV"]:
        likely_last = name_string.split(" ")[-2]
        #print('proposed last if suffix', likely_last)
        proposed_last = likely_last[:3]
    return proposed_last.upper()

def get_district(race_string, fill_level):
    race_string = race_string.split("-:-")[0]
    race_string = race_string.replace(" (Vote For 1)","")
    if "UNITED STATES REPRESENTATIVE" in race_string:
        break_word = "REPRESENTATIVE, "
        temp = race_string.split(break_word)[1]
        temp = re.findall('\d*', temp)[0]
    elif "STATE REPRESENTATIVE" in race_string or "STATE SENATOR" in race_string:
        break_word = "DISTRICT "
        temp = race_string.split(break_word)[1]
    else:
        raise ValueError
    
    return temp.zfill(fill_level)


def create_fips_col(csv_path, state_name_string, df, county_col_string):
    fips_file = pd.read_csv(csv_path)
    fips_file = fips_file[fips_file["State"] == state_name_string]
    fips_file["FIPS County"] = fips_file["FIPS County"].astype(str)
    fips_file["FIPS County"] = fips_file["FIPS County"].str.zfill(3)
    fips_file['County Name'] = fips_file['County Name'].apply(lambda x: x.replace(' ', ''))
    fips_file['County Name'] = fips_file['County Name'].apply(lambda x: str(x).lower())
    fips_dict = dict(zip(fips_file['County Name'], fips_file['FIPS County']))
    df['COUNTYFP'] = df[county_col_string].apply(lambda x: str(x).lower())
    df['COUNTYFP'] = df['COUNTYFP'].map(fips_dict).fillna(df[county_col_string])
    df['COUNTYFP'] = df['COUNTYFP'].astype(str)
    df['COUNTYFP'] = df['COUNTYFP'].str.zfill(3)
    return df

def full_readme_text(title, retrieval_date, source, fields_dict, github_link):

#First section of README
    readme_p1 = '''{title}\n
## RDH Date Retrieval
{retrieval_date}

## Sources
{source}

## Notes on Field Names (adapted from VEST):
Columns reporting votes generally follow the pattern: 
One example is:
G16PREDCLI
The first character is G for a general election, P for a primary, S for a special, and R for a runoff.
Characters 2 and 3 are the year of the election.*
Characters 4-6 represent the office type (see list below).
Character 7 represents the party of the candidate.
Characters 8-10 are the first three letters of the candidate's last name.

*To fit within the GIS 10 character limit for field names, the naming convention is slightly different for the State Legislature, Public Service Commissioners and US House of Representatives. All fields are listed below with definitions.

Office Codes Used:
A## - Proposed Statewide Amendement
AGR - Commissioner of Agriculture
ATG - Attorney General
AUD - State Auditor
BOE## - State Board of Education
GOV - Governor
PS# - Public Service Commissioner
SOS - Secretary Of State
USS - United States Senator
CON## - U.S. Congress
SL###  - State Legislative Lower
SU##  - State Legislative Upper
SSC - Associate Justice State Supreme Court

## Fields:
'''.format(title = title, source = source, retrieval_date = retrieval_date)

#Second section of README
    fields_table = pd.DataFrame.from_dict(fields_dict.items())
    fields_table.columns = ["Field Name", "Description"]
    readme_p2 = fields_table.to_string(formatters={'Description':'{{:<{}s}}'.format(fields_table['Description'].str.len().max()).format, 'Field Name':'{{:<{}s}}'.format(fields_table['Field Name'].str.len().max()).format}, index=False, justify = "left")

#Third section of README
    readme_p3 = '''\n
## Processing Steps
Visit the RDH GitHub and the processing script for this code [here]({github_link})

## Additional Notes

Please direct questions related to processing this dataset to info@redistrictingdatahub.org.
'''.format(github_link=github_link)
    
    full_readme = str(readme_p1)+str(readme_p2)+str(readme_p3)
    return full_readme