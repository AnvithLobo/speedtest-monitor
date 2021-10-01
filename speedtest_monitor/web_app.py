import json

import streamlit as st
import time
import numpy as np
import pandas as pd
from pathlib import Path
from database import global_init, get_possible_tests_total, db_get_countries, db_get_cities, gb_get_isp, \
    get_total_tests, get_country_from_city, get_speedtest_results, get_latest_data, get_total_data_consumption
import altair as alt
import plotly.express as px

ISP_NAME = "TEST"

st.set_page_config(
    page_title=f"{ISP_NAME} Speed Tests",
    page_icon="🦈",
    layout="wide",
    initial_sidebar_state="expanded",
)


def db_init():
    db_path = (Path(__file__).parent / ".." / 'secrets' / 'speedtest_log.sqlite').absolute()
    global_init(db_path.as_posix())


db_init()

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>

"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

COUNTRIES = db_get_countries()
CITY = db_get_cities()
ISP = gb_get_isp()

st.title('Spectra Speed Tests')
st.write(f"""```
current data collection period is from 2021-07-29 05:00 AM IST - 2021-07-30 11:11 AM IST
(there are some 2-3 hours of gaps with no data)
Currently Speedtest is run every 15 Minutes on {get_possible_tests_total()} servers taking about 10-12 minutes on average for each run.
Tests are currently live and updated every 15 minutes.
""")
st.write('-------------------------------------------------')

st.write("Test Details")
st.write(pd.DataFrame({
    "Countries": [len(COUNTRIES) - 1],
    "Cities": [len(CITY) - 1],
    "Speedtest Providers": [len(ISP) - 1],
    "Possible Tests": [get_possible_tests_total()],
    "Total tests done": [get_total_tests()],
    "Total Upload data consumed": get_total_data_consumption(upload=True),
    "Total Download data consumed": get_total_data_consumption(download=True)
}))

option_isp = st.sidebar.selectbox(
    'Filter ISP',
    ISP)

if option_isp:
    st.write('Selected ISP:', option_isp)

option_country = st.sidebar.selectbox(
    'Filter Country',
    db_get_countries(option_isp))

if option_country:
    st.write('Selected Country:', option_country)

if option_country:

    option_city = st.sidebar.selectbox(
        'Filter City',
        db_get_cities(option_isp, option_country))

    if option_city:
        st.write('Selected City:', option_city)

else:
    option_city = st.sidebar.selectbox(
        'Filter City',
        db_get_cities(option_isp))

    if option_city:
        st.write('Selected City:', option_city)

options = {
    'isp': option_isp or ISP[1],
    'city': option_city
}


def country_from_options():
    return db_get_countries(options['isp'])[1]


def city_from_options():
    print(options['isp'])
    if not option_isp:
        options['isp'] = gb_get_isp(country_filter=options['country'])[1]
    return db_get_cities(options['isp'], options['country'])[1]


if options['city']:
    options['country'] = get_country_from_city(options['city'])
else:
    options['country'] = option_country or country_from_options()

options['city'] = option_city or city_from_options()
st.write(f"\n\n************************\n ")

date_range = st.date_input("PICK date range", [])


def data_frame_maker(data):
    latency = []
    upload_speed = []
    download_speed = []
    date = []
    for item in data:
        latency.append(item['latency'])
        upload_speed.append(item['upload_speed'])
        download_speed.append(item['download_speed'])
        date.append(item['date'])

    return {
        'latency': latency,
        'upload (mbps)': upload_speed,
        'download (mbps)': download_speed,
        'date': date
    }


if not date_range or len(date_range) != 2:
    speedtest_data = get_speedtest_results(country=options['country'],
                                           city=options['city'],
                                           isp=options['isp'])
else:
    speedtest_data = get_speedtest_results(country=options['country'],
                                           city=options['city'],
                                           isp=options['isp'],
                                           date_start=date_range[0],
                                           date_stop=date_range[1]
                                           )


def json_print(data):
    return json.loads(json.dumps(data, default=str))


st.write(f'Total Tests Run for `{options["isp"]} {options["city"]}` : ', len(speedtest_data))
chart_data = pd.DataFrame(
    data_frame_maker(speedtest_data),
    columns=['latency', 'upload (mbps)', 'download (mbps)', 'date'])

chart_data = chart_data.rename(columns={'date': 'index'}).set_index('index')

fig = px.line(chart_data)

fig.update_layout(
    showlegend=True,
    margin=dict(l=1, r=1, b=1, t=1),

)

st.plotly_chart(fig, use_container_width=True)

st.write(f"\nNote: The straight lines in the ghraps are actually from no collected data on those dates."
         f"\n       You can Choose the date range to get have a deeper look at other date ranges.")

st.write(f"\n\n************************\n ")
"Real options"
st.write(options)

st.write(f"\n\n************************\n ")

if st.checkbox('Show old graph'):
    st.line_chart(chart_data, width=900, height=400)

if st.checkbox('Show raw data'):
    st.write(json_print(speedtest_data))


def gen_recent_chart(data):
    records_list = []
    for record in data:
        records_list.append([record['speedtest_server'], *record['data']])
    # print(records_list)
    data_frame = pd.DataFrame(records_list,
                              columns=['Server', 'Latency', 'Download', 'Upload'])
    return data_frame


if st.checkbox('Show recent speedtest'):
    length = st.slider('Records',
                       min_value=5,
                       max_value=30,
                       value=10,
                       step=1)
    st.write("Displaying last ", length, " records")
    recent_data = get_latest_data(length)
    pd_data_recent = gen_recent_chart(recent_data)
    recent_chart = px.bar(pd_data_recent, x='Server', y=['Latency', 'Download', 'Upload'], barmode='group', height=800)

    st.plotly_chart(recent_chart, use_container_width=True)
    if st.checkbox('Show recent raw data'):
        st.write(recent_data)
    pass
