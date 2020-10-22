import streamlit as st
import pandas as pd
import altair as alt
# import geopandas as gpd
import json

st.title("Chicago Crimes")

@st.cache  # add caching so we load the data only once
def load_data():
    crimes_url = "https://raw.githubusercontent.com/CMU-IDS-2020/a3-tomato-and-potato/master/Crimes_2019_Jan.csv"
    return pd.read_csv(crimes_url)

@st.cache
def load_map():
    map_url = "https://raw.githubusercontent.com/CMU-IDS-2020/a3-tomato-and-potato/master/Chicago_Community.json"
    return alt.topo_feature(map_url, 'Chicago_Community')

df = load_data()
geojson = load_map()

if st.checkbox('Show Raw Data'):
    st.write(df.head())

picked = alt.selection_multi(fields = ['Primary Type'])

type_chart = alt.Chart(df).mark_bar().encode(
    alt.Y('Primary Type:N', sort='-x'),
    alt.X('count():Q'),
    color = alt.condition(picked, alt.value('#1f77b4'), alt.value('lightgray')),
    tooltip = ['Primary Type', 'count()']
).add_selection(picked)

chicago_map = \
alt.Chart(df).transform_filter(picked).transform_aggregate(
    case_count='count()',
    groupby=['Community Area']
).transform_lookup(
    lookup='Community Area',
    from_=alt.LookupData(geojson, 'properties.area_numbe', ['properties.community', 'type', 'geometry']),
).mark_geoshape(
    stroke='white'
).encode(
    color='case_count:Q',
    tooltip=['community:N', 'case_count:Q']
).transform_lookup(
    lookup='Community Area',
    from_=alt.LookupData(geojson, 'properties.area_numbe', ['properties.community']),
    as_=['community']
)

arrest_map = \
alt.Chart(df).transform_filter(picked).transform_aggregate(
    case_count='count()',
    arrest_count='sum(Arrest)',
    groupby=['Community Area']
).transform_calculate(
    arrest_rate='datum.arrest_count / datum.case_count'
).transform_lookup(
    lookup='Community Area',
    from_=alt.LookupData(geojson, 'properties.area_numbe', ['properties.community', 'type', 'geometry']),
).mark_geoshape(
    stroke='white'
).encode(
    color='arrest_rate:Q',
    tooltip=['community:N', 'arrest_rate:Q']
).transform_lookup(
    lookup='Community Area',
    from_=alt.LookupData(geojson, 'properties.area_numbe', ['properties.community']),
    as_=['community']
)

brush = alt.selection_interval(encodings=['x'])

time_chart = \
alt.Chart(df).transform_filter(picked)\
.mark_area().encode(
    alt.X('monthdate(Date)'),
    alt.Y('count()'),
).properties(width=600)

heatmap = \
alt.Chart(df).transform_filter(picked).transform_filter(brush)\
.mark_rect().encode(
    alt.X('hours(Date):O', title='hour of day'),
    alt.Y('day(Date):O', title='date'),
    alt.Color('count()', title='Case Count'),
    tooltip=['hours(Date)', 'day(Date)', 'count()']
)

# location_chart = \
# alt.Chart(df).transform_filter(picked)\
# .mark_bar().encode(
#     alt.X('Location Description', sort='-y'),
#     alt.Y('count()')
# )

st.write(
    alt.vconcat(
        # alt.hconcat(
        #     type_chart,
        #     location_chart,
        # ),
        type_chart,
        chicago_map,
        arrest_map,
        time_chart.encode(
            alt.X('monthdate(Date)', scale=alt.Scale(domain=brush))
        ),
        alt.layer(
            time_chart.add_selection(brush).encode(
                color=alt.value('lightgray')
            ),
            time_chart.transform_filter(brush)
        ),
        heatmap
    ).resolve_scale(color='independent')
)

picked = alt.selection_multi(fields=['Community Area'])

chicago_map = \
alt.Chart(df).transform_aggregate(
    case_count='count()',
    groupby=['Community Area']
).transform_lookup(
    lookup='Community Area',
    from_=alt.LookupData(geojson, 'properties.area_numbe', ['properties.community', 'type', 'geometry']),
).mark_geoshape(
    stroke='white'
).encode(
    color=alt.condition(picked, 'case_count:Q', alt.value('lightgray')),
    tooltip=['community:N', 'case_count:Q']
).transform_lookup(
    lookup='Community Area',
    from_=alt.LookupData(geojson, 'properties.area_numbe', ['properties.community']),
    as_=['community']
).add_selection(picked)

type_chart = \
alt.Chart(df)\
.mark_bar().encode(
    alt.Y('Primary Type:N', sort='-x'),
    alt.X('count():Q'),
    tooltip = ['Primary Type', 'count()']
)

heatmap = \
alt.Chart(df).transform_filter(picked)\
.mark_rect().encode(
    alt.X('hours(Date):O', title='hour of day'),
    alt.Y('day(Date):O', title='date'),
    alt.Color('count()', title='Case Count'),
    tooltip=['hours(Date)', 'day(Date)', 'count()']
)

st.write(
    alt.vconcat(
        chicago_map,
        alt.layer(
            type_chart.encode(color = alt.value('lightgray')),
            type_chart.transform_filter(picked)
        ),
        heatmap
    ).resolve_scale(color='independent')
)