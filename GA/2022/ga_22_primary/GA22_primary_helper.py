import geopandas as gp
import pandas as pd
import os
import xml.etree.ElementTree as et
import numpy as np
import re

#Peter's xml parser for clarity elections' county by county election returns
def ph_clarityelec_xml(str_datalocation, str_electype):
    loaded_counties = os.listdir(str_datalocation)
    z=[]
    for locale in loaded_counties:
        if locale.endswith('.xml'):
            file_string = "./raw-from-source/counties/"+locale
            xtree = et.parse(file_string)
            xroot = xtree.getroot()
            store_list = []
            county_area = xroot.findall(".//Region")
            for i in county_area:
                county = i.text
        contests = xroot.findall(".//Contest")
        for i in contests:
            contest = i.attrib.get('text')
            lower = i.findall("./Choice")
            for j in lower:
                choice = j.attrib.get('text')
                lower_2 = j.findall("./VoteType")
                for k in lower_2:
                    voting_method = k.attrib.get('name')
                    lower_3 = k.findall("./Precinct")
                    for l in lower_3:
                        precinct_name = l.attrib.get('name')
                        num_votes = l.attrib.get('votes')
                        z.append([county,contest,choice,voting_method,precinct_name,num_votes])
    dfcols = ['county','contest','choice','voting_method','precinct','num_votes']
    df_ = pd.DataFrame(z,columns=dfcols)
    df_["election"] = str_electype
    df_["precinct"] = df_["precinct"].str.strip()
    return df_

#subset contests by a list of keywords
def contests_to_keep(all_contests, keywords_list):
    keep_contests = []
    for item in keywords_list:
        temp_str = '.*' + item
        r= re.compile(temp_str)
        item_list = list(filter(r.match, all_contests))
        keep_contests += item_list
    return keep_contests


'''
Slight adaptation of Peter's functions for VEST style column renaming

'''
def get_race(race_string):
    race = ''
    race_string = race_string.title()
    if "U.S. House" in race_string or 'Us House' in race_string:
        race = "CON"
    elif "State House" in race_string:
        race =  "SL"
    elif "State Senate" in race_string:
        race = "SU"
    elif "President" in race_string:
        race = "PRE"
    elif "US Senate" in race_string or "Us Senate" in race_string:
        race = "USS"
    elif "Public Service" in race_string:
        race = "PSC"
    elif "Attorney General" in race_string:
        race = "ATG"
    elif "Auditor General" in race_string:
        race = "AUD"
    elif "Treasurer" in race_string:
        race = "TRE"
    elif "Superintendent" in race_string:
        race = "SUP"
    elif "Secretary Of State" in race_string:
        race = "SOS"
    elif "Lieutenant Governor" in race_string:
        race = "LTG"
    elif "Governor" in race_string:
        race = "GOV"
    elif "Commissioner Of Labor" in race_string:
        race = "LAB"
    elif "Commissioner Of Agriculture" in race_string:
        race = "AGR"
    elif "Commissioner Of Insurance" in race_string:
        race = "INS"
    elif "State School Superintendent" in race_string:
        race = "SUP"
    elif "Public Service Commissioner" in race_string:
        race = "PSC"
    elif "Supreme Court" in race_string:
        race = "SSC"
    elif "Court of Appeals" in race_string:
        race = "COA"
    if any(word in race_string for word in ['US House', 'State House', 'State Senate', 'Public Service Commissioner']):
        return race +''.join(filter(str.isdigit, race_string))
    else:
        return race


def get_election_type_year(race_string):
    if "Supreme Court" in race_string:
         electype = "S"
    else:
        electype = "P"
    if any(word in race_string for word in ['US House', 'State House', 'State Senate', 'Public Service Commissioner', 'PSC']):
        return electype
    else:
        return electype +"22"
    
def get_party(race_string):
    race_string = race_string.lower()
    if "Rep" in race_string:
        return "R"
    elif "Dem" in race_string:
        return "D"
    elif "Supreme Court" in race_string or "Court of Appeals" in race_string:
        return "N"

def get_name(name_string):
    name_string = name_string.split("-:-")[1]
    name_string = name_string.replace("'","")
    name_string = name_string.replace(',','')
    if name_string.split(" ")[-1] in ['II', 'III', 'Jr', 'Jr.', 'Sr.', 'JR.', "JR", "IV"]:
            likely_last = name_string.split(" ")[-2]
    else:
        likely_last = name_string.split(" ")[-1]
    return likely_last[:3].upper()

def get_district(race_string):
    if any(word in race_string for word in ['US House', 'State House', 'State Senate', 'Public Service Commissioner']):
        return''.join(filter(str.isdigit, race_string))
    else:
        return str()
    
def sanity_check():
    print('This is a sanity check.')
    
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
AGR - Commissioner of Agriculture
ATG - Attorney General
GOV - Governor
INS - Commissioner Of Insurance
LAB - Commissioner Of Labor
LTG - Lieutenant Governor
PSC# - Public Service Commissioner
SOS - Secretary Of State
SUP - State School Superintendent
USS - U.S. Senate
CON## - U.S. Congress
SL###  - State Legislative Lower
SU##  - State Legislative Upper
SSC - State Supreme Court
COA - State Court of Appeals

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
Files were checked against separate statewide and countywide election result files also available from the Georgia Secretary of State. Results matched exactly except for differences below.

Georgia Secretary of State summary files had no reported votes for the following contests:
Cook County - G22COANBAR, G22COANMCF, G22COANPIP, G22SSSCNMCM, G22SSCNLAG, G22SSCNCOL, G22SSCNBRI
Grady County - PCON02DBIS
Mitchell County - PCON02DBIS
Thomas County - PSL173RTAY, PSL173DSR
In all instances where the SOS county-level file had no reported votes in a contest in a specific county, vote numbers from the precinct-level compiled dataset are presumed to be accurate and included in this dataset.

Georgia Secretary of State summary files had no reported data for the following contest:
Grady County - PCON02DOHA
Mitchell County - PCON02DOHA
In this instance, we believe this candidate received zero votes in these counties because votes for other candidates were reported at the precinct level in this contest.
However, we are unable to confirm, since there is no reported data for this candidate, in these counties.

Georgia Secretary of State summary files had equal vote total discrepancies in the following contests:
Pickens County - 9 votes swapped between G22SSCNMCM and G22SSCNLAG contests
Whitfield County - 16 votes swapped between G22SSCNMCM and G22SSCNLAG contests
The vote discrepancies in Pickens and Whitfield county seem to indicate swapping of 9 and 16 votes in each county respectively. We are unable to determine whether this error originated at the precinct, or county level. Given the differences found in other contests in the Secretary of State's county-level file, we are unable to support it's accuracy. We have chosen to leave the precinct-level vote totals unaltered in these contests.

Please direct questions related to processing this dataset to info@redistrictingdatahub.org.
'''.format(github_link=github_link)
    
    full_readme = str(readme_p1)+str(readme_p2)+str(readme_p3)
    return full_readme