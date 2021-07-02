# WHO cases for streamlit

# Import modules
import streamlit as st
import os
import pandas as pd
import numpy as np
import datetime
from datetime import date
import requests
#import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fuzzywuzzy import fuzz
# from PIL import Image

pd.options.plotting.backend = "plotly"

st.set_page_config(page_title='WHO COVID statistics',
                   page_icon='./images/icon.ico', layout='wide', initial_sidebar_state='auto')

# Auxiliary function
def argmax(iterable):
    return max(enumerate(iterable), key=lambda x: x[1])[0]

# Fetch data
url = 'https://covid19.who.int/WHO-COVID-19-global-data.csv'
cases_file_path = "./data/who-cases.csv"
stat = os.stat(cases_file_path)
dt_file = date.fromtimestamp(os.path.getmtime(cases_file_path))


@st.cache
def get_data():
    response = requests.get(url)
    if dt_file != date.today():
        response = requests.get(url)
        with open(cases_file_path, 'wb') as f:
            f.write(response.content)
    df = pd.read_csv(cases_file_path)
    return df


df_ = get_data()
df = df_.copy()
df['Country'] = df['Country'].apply(lambda x: x.title())
df.Date_reported = pd.to_datetime(df.Date_reported)

# One country
country_group = df.groupby(['Country_code'])
# List of codes
codes = df['Country_code'].fillna('MA').unique()
countries = df['Country'].unique()
exists = False
# Get user input
while not exists:
    code = st.text_input('Country or country code:', value='RU',
                         help='Codes are two-letter abbreviations, e.g. ES for Spain. Minor typos in countries names are forgiven)))')
    if (code.upper() in codes) or (code.title() in countries):
        exists = True
    else:
        code = countries[argmax(
            list(map(lambda x: fuzz.token_set_ratio(x, code.title()), countries)))]
        exists = True
        #print('No such country in the dataset, \nPlease try again...')

if len(code) <= 3:
    df_c = country_group.get_group(code.upper())
    country = df_c['Country'].iloc[0]
else:
    country = code.title()
    code = df[df['Country'] == code.title()]['Country_code'].iloc[0]
    df_c = country_group.get_group(code)

# Calculations
df_country = df_c.drop(['Country', 'WHO_region'], axis=1)
df_country['New_cases'] = df_country['New_cases'].rolling(7).mean()
df_country['Pct_deaths'] = 100*df_country.New_deaths.rolling(7).mean() / (
    df_country.New_cases + 1)
df_country['New_deaths'] = 50*df_country.New_deaths.rolling(7).mean()
df_country.round({'New_cases': 0, 'New_deaths': 0, 'Pct_deaths': 1})

# Create figure with secondary y-axis
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Add traces
fig.add_trace(
    go.Scatter(x=df_country['Date_reported'],
               y=df_country['New_cases'], name="New cases"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=df_country['Date_reported'],
               y=df_country['New_deaths'], name="New deaths x 50"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=df_country['Date_reported'], y=df_country['Pct_deaths'], name="Pct deaths", line=dict(color='green', width=2, dash='dot')), secondary_y=True
)
# Add figure title
fig.update_layout(
    title_text=f'<b>COVID</b>, new cases and deaths in <b>{country}</b>'
)
fig.update_yaxes(ticksuffix="%", secondary_y=True)
# Set x-axis title
fig.update_xaxes(title_text="<b>date reported</b>")
# Set y-axes titles
fig.update_yaxes(title_text="new <b>cases</b>", secondary_y=False)
fig.update_yaxes(title_text="<b>pct deaths</b> to cases", secondary_y=True)


# fig.show()
st.plotly_chart(fig, use_container_width=True)
# Dataframe to show
df_st = df_c.drop(columns=['Country_code', 'Country', 'WHO_region'])
df_st['Date_reported'] = df_st['Date_reported'].apply(
    lambda x: x.strftime("%d.%m.%Y"))
# df_st['New_deaths']=df_st['New_deaths']
df_st.set_index('Date_reported', inplace=True)
# df_st.style.format('{:n}')
st.markdown(f'Raw data for **{country}**')
df_st.rename(columns={'New_cases': 'New cases', 'Cumulative_cases': 'Cumulative cases',
                      'New_deaths': 'New deaths', 'Cumulative_deaths': 'Cumulative deaths'},
             inplace=True)
df_disp = df_st.T  # horizontal df

df_disp.iloc[:, -10::]  # last 10 days