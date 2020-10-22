import streamlit as st
import pandas as pd
import altair as alt
# import geopandas as gpd
# import json

st.title("Chicago Crimes")

@st.cache  # add caching so we load the data only once
def load_data():
    crimes_url = "https://raw.githubusercontent.com/CMU-IDS-2020/a3-tomato-and-potato/master/Crimes_2019.csv"
    return pd.read_csv(crimes_url).sample(n=50000)

@st.cache
def load_map():
    map_url = "https://raw.githubusercontent.com/CMU-IDS-2020/a3-tomato-and-potato/master/Chicago_Community.json"
    return alt.topo_feature(map_url, 'Chicago_Community')

df = load_data()
geojson = load_map()

# if st.checkbox('Show Raw Data'):
#     st.write(df.head())

picked = alt.selection_multi(fields = ['Primary Type'])

type_chart = alt.Chart(df).mark_bar().encode(
    alt.Y('Primary Type:N', sort='-x'),
    alt.X('count():Q'),
    color = alt.condition(picked, "Location Description", alt.value('lightgray')),
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
    color=alt.Color('arrest_rate:Q', scale=alt.Scale(domain=[0, 0.5, 1.0], scheme='yellowgreenblue')),
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
    alt.X('yearmonth(Date)'),
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

st.write("## How is crime distributed?")
st.write(
    alt.vconcat(
        type_chart.properties(
            width=400,
            title='Crime Type Count'
        ),
        alt.hconcat(
            chicago_map.properties(
                width=200,
                title='Crime Count in Communities'
            ),
            arrest_map.properties(
                width=200,
                title='Arrest Rate in Communities'
            ),
        ).resolve_scale(color='independent'),
        time_chart.encode(
            alt.X('yearmonthdate(Date)', scale=alt.Scale(domain=brush))
        ),
        alt.layer(
            time_chart.add_selection(brush).encode(
                color=alt.value('lightgray')
            ),
            time_chart.transform_filter(brush).properties(
                height=100,
            )
        ),
        heatmap.properties(
            width=600,
            title="Crime Time heatmap"
        )
    ).resolve_scale(color='independent')
)

st.write("## Where do you live?")
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
).properties(title="Crime Type total count")

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
        chicago_map.properties(
            title='Crime Case for Communities'
        ),
        alt.layer(
            type_chart.encode(color = alt.value('lightgray')),
            type_chart.transform_filter(picked)
        ),
        heatmap.properties(
            width=600,
            title="Crime Time heatmap"
        )
    ).resolve_scale(color='independent')
)